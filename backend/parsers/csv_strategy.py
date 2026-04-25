import pandas as pd
import io
import re
import logging
from typing import List, Dict, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app.schemas.normalization import UnifiedTransaction
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class CSVStrategy(BaseStrategy):

    # --- Keyword banks for auto-detection (all lowercase) ---
    DATE_KEYWORDS = ['date', 'posting', 'trx', 'transaction', 'txn', 'valued']
    AMOUNT_KEYWORDS = ['amount', 'value', 'sum', 'total', 'amt']
    DESC_KEYWORDS = ['desc', 'detail', 'memo', 'narration', 'particular', 'remark', 'note']
    REF_KEYWORDS = ['ref', 'transid', 'txnid', 'id', 'reference', 'cheque', 'check', 'number']
    ACTION_KEYWORDS = ['action', 'type', 'dr/cr', 'drcr', 'indicator']
    DEBIT_KEYWORDS = ['debit', 'dr', 'withdrawal', 'paid out', 'outflow']
    CREDIT_KEYWORDS = ['credit', 'cr', 'deposit', 'paid in', 'inflow']

    @staticmethod
    def _match_column(columns: List[str], keywords: List[str], exclude: set = None) -> Optional[str]:
        """
        Find the best matching column using a multi-pass approach:
        1. Exact match (case-insensitive)
        2. Word boundary match (for short keywords like 'cr', 'dr')
        3. Substring match (for longer keywords)
        """
        exclude = exclude or set()
        
        def normalize(s):
            return s.lower().replace('_', ' ').replace('-', ' ').strip()

        cols_norm = [(col, normalize(col)) for col in columns if col not in exclude]

        # Pass 1: Exact matches
        for col, norm in cols_norm:
            if norm in keywords:
                return col

        # Pass 2: Word Boundary matches for short keywords
        for kw in keywords:
            for col, norm in cols_norm:
                if len(kw) <= 3:
                    # e.g. 'cr' should match 'cr' or 'cr amount' but NOT 'description'
                    if re.search(rf'\b{re.escape(kw)}\b', norm):
                        return col
        
        # Pass 3: Substring matches for longer keywords
        for kw in keywords:
            if len(kw) > 3:
                for col, norm in cols_norm:
                    if kw in norm:
                        return col
        
        return None

    def _auto_detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        cols = list(df.columns)
        mapping = {}
        used = set()

        # 1. Date
        date_col = self._match_column(cols, self.DATE_KEYWORDS, used)
        if date_col:
            mapping['date'] = date_col
            used.add(date_col)

        # 2. Amount (single signed column)
        amount_col = self._match_column(cols, self.AMOUNT_KEYWORDS, used)
        if amount_col:
            mapping['amount'] = amount_col
            used.add(amount_col)

        # 3. Action (DR/CR indicator)
        action_col = self._match_column(cols, self.ACTION_KEYWORDS, used)
        if action_col:
            mapping['action'] = action_col
            used.add(action_col)

        # 4. Debit/Credit pair
        if 'amount' not in mapping:
            debit_col = self._match_column(cols, self.DEBIT_KEYWORDS, used)
            credit_col = self._match_column(cols, self.CREDIT_KEYWORDS, used)
            if debit_col and credit_col:
                mapping['debit'] = debit_col
                mapping['credit'] = credit_col
                used.add(debit_col)
                used.add(credit_col)

        # 5. Description
        desc_col = self._match_column(cols, self.DESC_KEYWORDS, used)
        if desc_col:
            mapping['description'] = desc_col
            used.add(desc_col)

        # 6. Reference
        ref_col = self._match_column(cols, self.REF_KEYWORDS, used)
        if ref_col:
            mapping['ref'] = ref_col
            used.add(ref_col)

        return mapping

    def parse(self, content: bytes, column_mapping: Dict[str, str] = None) -> List[UnifiedTransaction]:
        # 1. Load into DataFrame with auto-delimiter detection
        try:
            # Try UTF-8 with BOM first, then fallback
            try:
                decoded_content = content.decode('utf-8-sig')
                df = pd.read_csv(io.StringIO(decoded_content), sep=None, engine='python')
            except:
                df = pd.read_csv(io.BytesIO(content), sep=None, engine='python')
        except Exception as e:
            try:
                df = pd.read_excel(io.BytesIO(content))
            except Exception as ex:
                raise ValueError(f"Could not parse file: {str(e)} / {str(ex)}")

        if column_mapping is None:
            column_mapping = {}

        # 2. Validation and Auto-detection
        needs_auto = False
        if not column_mapping:
            needs_auto = True
        else:
            for key in ['date', 'amount']:
                if key in column_mapping and column_mapping[key] not in df.columns:
                    needs_auto = True
                    break

        if needs_auto:
            detected = self._auto_detect_columns(df)
            for key, val in detected.items():
                if key not in column_mapping or column_mapping[key] not in df.columns:
                    column_mapping[key] = val

        # 3. Final validation
        if 'date' not in column_mapping or column_mapping['date'] not in df.columns:
            raise ValueError(f"Could not detect Date column. Headers: {list(df.columns)}")

        has_amount = 'amount' in column_mapping and column_mapping['amount'] in df.columns
        has_debit_credit = (
            'debit' in column_mapping and column_mapping['debit'] in df.columns and
            'credit' in column_mapping and column_mapping['credit'] in df.columns
        )
        has_action = 'action' in column_mapping and column_mapping['action'] in df.columns

        if not has_amount and not has_debit_credit:
            raise ValueError(f"Could not detect Amount or Debit/Credit columns. Headers: {list(df.columns)}")

        # Determine mode
        if has_debit_credit:
            amount_mode = 'debit_credit'
        elif has_amount and has_action:
            amount_mode = 'value_action'
        else:
            amount_mode = 'signed'

        # Default description
        if 'description' not in column_mapping or column_mapping['description'] not in df.columns:
            used_cols = set(column_mapping.values())
            for col in df.columns:
                if col not in used_cols and df[col].dtype == 'object':
                    column_mapping['description'] = col
                    break

        # 4. Iterate and Normalize
        transactions = []
        for index, row in df.iterrows():
            try:
                # --- Date ---
                raw_date = str(row[column_mapping['date']])
                try:
                    date_obj = pd.to_datetime(raw_date).date()
                except Exception as e:
                    logger.warning(f"Row {index}: Invalid date '{raw_date}' - skipping. Error: {e}")
                    continue

                # --- Amount ---
                if amount_mode == 'debit_credit':
                    credit_val = self._clean_amount(row[column_mapping['credit']])
                    debit_val = self._clean_amount(row[column_mapping['debit']])
                    amount = credit_val - debit_val
                elif amount_mode == 'value_action':
                    raw_val = self._clean_amount(row[column_mapping['amount']])
                    action = str(row[column_mapping['action']]).strip().upper()
                    amount = -abs(raw_val) if action in ('DR', 'DEBIT', 'D') else abs(raw_val)
                else:
                    amount = self._clean_amount(row[column_mapping['amount']])

                # --- Description & Ref ---
                desc_col = column_mapping.get('description')
                description = str(row[desc_col]).strip() if desc_col and desc_col in df.columns else ""
                
                ref_col = column_mapping.get('ref')
                ref_id = str(row[ref_col]).strip() if ref_col and ref_col in df.columns else f"CSV-{index}"

                transactions.append(UnifiedTransaction(
                    date=date_obj,
                    amount=amount,
                    description=description,
                    external_ref_id=ref_id,
                    raw_source="CSV_ROW",
                    source_format="csv_excel"
                ))

            except Exception as e:
                logger.error(f"Row {index} failed to parse: {str(e)}")
                continue

        return transactions

    @staticmethod
    def _clean_amount(val) -> Decimal:
        """Robustly clean numeric strings into Decimals."""
        if pd.isna(val) or val is None:
            return Decimal(0)
        
        s = str(val).strip().replace('$', '').replace(' ', '')
        if not s or s.lower() in ('nan', 'none', ''):
            return Decimal(0)

        # Handle parentheses
        if s.startswith('(') and s.endswith(')'):
            s = '-' + s[1:-1]

        # Handle EU/US formats
        comma_count = s.count(',')
        dot_count = s.count('.')
        
        if comma_count > 0 and dot_count > 0:
            if s.rfind(',') > s.rfind('.'): # EU style: 1.234,56
                s = s.replace('.', '').replace(',', '.')
            else: # US style: 1,234.56
                s = s.replace(',', '')
        elif comma_count > 0:
            # If multiple commas, they are thousand separators
            if comma_count > 1:
                s = s.replace(',', '')
            # If one comma, check if it's likely a decimal (e.g., 12,34)
            elif len(s.split(',')[1]) == 2:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        elif dot_count > 1:
            s = s.replace('.', '')

        try:
            return Decimal(s)
        except (InvalidOperation, ValueError):
            return Decimal(0)
