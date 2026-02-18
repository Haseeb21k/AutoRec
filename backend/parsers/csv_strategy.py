import pandas as pd
import io
from typing import List, Dict, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app.schemas.normalization import UnifiedTransaction
from .base_strategy import BaseStrategy


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
        Find the first column whose lowercased name contains any of the keywords.
        Returns the original column name (preserving case).
        """
        exclude = exclude or set()
        for col in columns:
            if col in exclude:
                continue
            col_lower = col.lower().replace('_', ' ').replace('-', ' ')
            for kw in keywords:
                if kw in col_lower:
                    return col
        return None

    def _auto_detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Scans DataFrame headers and classifies them by role using keyword matching.
        Returns a mapping like {'date': 'TransactionDate', 'amount': 'Value', ...}
        """
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

        # 3. Action (DR/CR indicator — used together with amount/value)
        action_col = self._match_column(cols, self.ACTION_KEYWORDS, used)
        if action_col:
            mapping['action'] = action_col
            used.add(action_col)

        # 4. Debit/Credit pair (if no single amount column found)
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

        # 6. Reference / Transaction ID
        ref_col = self._match_column(cols, self.REF_KEYWORDS, used)
        if ref_col:
            mapping['ref'] = ref_col
            used.add(ref_col)

        return mapping

    def parse(self, content: bytes, column_mapping: Dict[str, str] = None) -> List[UnifiedTransaction]:
        """
        Parses CSV or Excel bytes into standardized UnifiedTransaction objects.
        Supports auto-detection of columns when mapping is incomplete or wrong.
        """
        # 1. Load into DataFrame
        try:
            df = pd.read_csv(io.BytesIO(content))
        except:
            try:
                df = pd.read_excel(io.BytesIO(content))
            except Exception as e:
                raise ValueError(f"Could not parse file as CSV or Excel: {str(e)}")

        if column_mapping is None:
            column_mapping = {}

        # 2. Validate provided mapping against actual headers
        #    If any mapped column doesn't exist, fall back to auto-detection
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
            # Merge: detected values fill in gaps, don't overwrite valid user mappings
            for key, val in detected.items():
                if key not in column_mapping or column_mapping[key] not in df.columns:
                    column_mapping[key] = val

        # 3. Final validation — we MUST have date and some amount source
        if 'date' not in column_mapping or column_mapping['date'] not in df.columns:
            raise ValueError(
                f"Could not detect a Date column. Headers found: {list(df.columns)}"
            )

        has_amount = 'amount' in column_mapping and column_mapping['amount'] in df.columns
        has_debit_credit = (
            'debit' in column_mapping and column_mapping['debit'] in df.columns and
            'credit' in column_mapping and column_mapping['credit'] in df.columns
        )
        has_action = 'action' in column_mapping and column_mapping['action'] in df.columns

        if not has_amount and not has_debit_credit:
            raise ValueError(
                f"Could not detect Amount or Debit/Credit columns. Headers found: {list(df.columns)}"
            )

        # Determine amount mode
        if has_debit_credit:
            amount_mode = 'debit_credit'
        elif has_amount and has_action:
            amount_mode = 'value_action'
        else:
            amount_mode = 'signed'

        # Default description to first available text-ish column if not found
        if 'description' not in column_mapping or column_mapping['description'] not in df.columns:
            # Pick any remaining string column that isn't already used
            used_cols = set(column_mapping.values())
            for col in df.columns:
                if col not in used_cols and df[col].dtype == 'object':
                    column_mapping['description'] = col
                    break

        # 4. Iterate and Normalize
        transactions = []
        for index, row in df.iterrows():
            try:
                # --- Date Parsing ---
                raw_date = str(row[column_mapping['date']])
                try:
                    date_obj = pd.to_datetime(raw_date).date()
                except:
                    continue  # Skip rows with invalid dates

                # --- Amount Parsing ---
                if amount_mode == 'debit_credit':
                    credit_val = self._clean_amount(row[column_mapping['credit']])
                    debit_val = self._clean_amount(row[column_mapping['debit']])
                    amount = credit_val - debit_val

                elif amount_mode == 'value_action':
                    raw_val = self._clean_amount(row[column_mapping['amount']])
                    action = str(row[column_mapping['action']]).strip().upper()
                    # DR = debit (money out = negative), CR = credit (money in = positive)
                    if action in ('DR', 'DEBIT', 'D'):
                        amount = -abs(raw_val)
                    else:
                        amount = abs(raw_val)

                else:  # signed
                    raw_amount = str(row[column_mapping['amount']])
                    clean_str = raw_amount.replace('$', '').replace(',', '').replace(' ', '')
                    # Handle parentheses for negative: (500.00) -> -500.00
                    if '(' in clean_str and ')' in clean_str:
                        clean_str = '-' + clean_str.replace('(', '').replace(')', '')
                    if not clean_str or clean_str == 'nan':
                        continue
                    amount = Decimal(clean_str)

                # --- Description Parsing ---
                desc_col = column_mapping.get('description')
                description = str(row[desc_col]).strip() if desc_col and desc_col in df.columns else ""

                # --- Reference ID ---
                ref_col = column_mapping.get('ref')
                if ref_col and ref_col in df.columns:
                    ref_id = str(row[ref_col]).strip()
                else:
                    ref_id = f"CSV-{index}"

                transactions.append(UnifiedTransaction(
                    date=date_obj,
                    amount=amount,
                    description=description,
                    external_ref_id=ref_id,
                    raw_source="CSV_ROW",
                    source_format="csv_excel",
                    confidence_score=1.0
                ))

            except (ValueError, InvalidOperation, IndexError, KeyError):
                continue

        return transactions

    @staticmethod
    def _clean_amount(val) -> Decimal:
        """Clean a cell value into a Decimal. Returns 0 for empty/NaN."""
        s = str(val).replace('$', '').replace(',', '').replace(' ', '')
        if not s or s == 'nan' or s == 'None' or s == '':
            return Decimal(0)
        return Decimal(s)
