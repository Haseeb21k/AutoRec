import pandas as pd
import io
from typing import List, Dict
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app.schemas.normalization import UnifiedTransaction
from .base_strategy import BaseStrategy

class CSVStrategy(BaseStrategy):
    def parse(self, content: bytes, column_mapping: Dict[str, str]) -> List[UnifiedTransaction]:
        """
        Parses CSV or Excel bytes into standardized UnifiedTransaction objects.
        """
        # 1. Detect format and load into Pandas DataFrame
        try:
            # Try reading as CSV first
            df = pd.read_csv(io.BytesIO(content))
        except:
            try:
                # Fallback to Excel
                df = pd.read_excel(io.BytesIO(content))
            except Exception as e:
                raise ValueError(f"Could not parse file as CSV or Excel: {str(e)}")

        transactions = []
        
        # 2. Validate Mapping & Detect Columns
        # We allow 'amount' OR ('debit' AND 'credit')
        use_debit_credit = False
        
        # Check Date
        if 'date' not in column_mapping:
             raise ValueError("Missing mapping for required field: date")
        if column_mapping['date'] not in df.columns:
             # Try common variations cause users are bad at mapping
             found_date = False
             for guess in ['Date', 'Posting Date', 'Trx Date', 'date']:
                 if guess in df.columns:
                     column_mapping['date'] = guess
                     found_date = True
                     break
             if not found_date:
                 raise ValueError(f"Mapped column '{column_mapping['date']}' not found in headers: {list(df.columns)}")

        # Check Description
        if 'description' not in column_mapping:
             column_mapping['description'] = 'Description' # Default
        if column_mapping['description'] not in df.columns:
             # Try to find a description column
             for guess in ['Description', 'Memo', 'Details', 'Narration']:
                 if guess in df.columns:
                     column_mapping['description'] = guess
                     break

        # Check Amount
        if 'amount' in column_mapping and column_mapping['amount'] in df.columns:
            use_debit_credit = False
        else:
            # Check for Debit/Credit pair
            # We look for ANY pair of columns that look like debit/credit
            debit_candidates = ['Debit', 'Dr', 'Withdrawal', 'Paid Out']
            credit_candidates = ['Credit', 'Cr', 'Deposit', 'Paid In']
            
            debit_col = next((c for c in debit_candidates if c in df.columns), None)
            credit_col = next((c for c in credit_candidates if c in df.columns), None)
            
            if debit_col and credit_col:
                use_debit_credit = True
                column_mapping['debit'] = debit_col
                column_mapping['credit'] = credit_col
            else:
                 # Last ditch effort: maybe the user mapped 'amount' but the file uses 'Amount ($)'?
                 # For now, strict fail if we can't find anything
                 if 'amount' in column_mapping:
                    raise ValueError(f"Mapped column '{column_mapping['amount']}' not found. Also could not find Debit/Credit pair.")
                 else:
                    raise ValueError("Could not auto-detect Amount or Debit/Credit columns.")

        # 3. Iterate and Normalize
        for index, row in df.iterrows():
            try:
                # --- Date Parsing ---
                raw_date = str(row[column_mapping['date']])
                # Attempt standard formats. In production, use a robust date parser.
                try:
                    date_obj = pd.to_datetime(raw_date).date()
                except:
                    # Skip rows with invalid dates (often header metadata rows in bank files)
                    continue

                # --- Amount Parsing ---
                if use_debit_credit:
                    # Logic: Amount = Credit (Positive) - Debit (Positive)
                    # We assume values in columns are positive magnitudes
                    def clean_val(val):
                        s = str(val).replace('$', '').replace(',', '').replace(' ', '')
                        if not s or s == 'nan' or s == 'None': return Decimal(0)
                        return Decimal(s) if s else Decimal(0)

                    credit_val = clean_val(row[column_mapping['credit']])
                    debit_val = clean_val(row[column_mapping['debit']])
                    amount = credit_val - debit_val
                else:
                    # Existing Logic
                    raw_amount = str(row[column_mapping['amount']])
                    # Clean currency symbols ($ ,) and spaces
                    clean_amount_str = raw_amount.replace('$', '').replace(',', '').replace(' ', '')
                    
                    # Handle parentheses for negative: (500.00) -> -500.00
                    if '(' in clean_amount_str and ')' in clean_amount_str:
                        clean_amount_str = '-' + clean_amount_str.replace('(', '').replace(')', '')
                    
                    if not clean_amount_str or clean_amount_str == 'nan':
                        continue
                        
                    amount = Decimal(clean_amount_str)

                # --- Description Parsing ---
                description = str(row[column_mapping['description']]).strip()

                transactions.append(UnifiedTransaction(
                    date=date_obj,
                    amount=amount,
                    description=description,
                    external_ref_id=f"CSV-{index}", # Placeholder
                    raw_source="CSV_ROW",
                    source_format="csv_excel",
                    confidence_score=1.0
                ))

            except (ValueError, InvalidOperation, IndexError):
                # If a specific row fails (e.g., total line at bottom), skip it
                continue

        return transactions
