import re
from typing import List
from decimal import Decimal
from datetime import datetime
from app.schemas.normalization import UnifiedTransaction
from .base_strategy import BaseStrategy

class MT940Strategy(BaseStrategy):
    def __init__(self):
        # Regex pre-compilation for performance
        self.line_61_pattern = re.compile(r":61:(\d{6})(\d{4})?([CD])([\d,]+)")

    def parse(self, content: str, **kwargs) -> List[UnifiedTransaction]:
        """
        Parses MT940 string and returns normalized UnifiedTransaction objects.
        """
        transactions = []
        lines = content.splitlines()
        current_data = None
        
        for line in lines:
            line = line.strip()
            
            # --- Parse Transaction Line (:61:) ---
            if line.startswith(":61:"):
                # Save previous transaction if it exists
                if current_data:
                    transactions.append(UnifiedTransaction(**current_data))
                
                match = self.line_61_pattern.match(line)
                if match:
                    raw_date = match.group(1)   # Format: YYMMDD
                    entry_date = match.group(2) # Optional
                    dc_mark = match.group(3)    # C or D
                    raw_amount = match.group(4).replace(",", ".")

                    # Convert Amount to Decimal (Financial Standard)
                    amount = Decimal(raw_amount)
                    
                    # Logic: If Debit (D), amount should be negative
                    if dc_mark == 'D':
                        amount = -amount

                    # Convert Date to YYYY-MM-DD
                    date_obj = datetime.strptime(raw_date, "%y%m%d").date()
                    
                    # Initial data dict
                    current_data = {
                        "date": date_obj,
                        "amount": amount,
                        "description": "No Description", # Default
                        "external_ref_id": f"MT940-{raw_date}-{len(transactions)}",
                        "raw_source": line,
                        "source_format": "mt940",
                        "confidence_score": 1.0
                    }

            # --- Parse Description Line (:86:) ---
            elif line.startswith(":86:") and current_data:
                # Remove the tag and whitespace
                description = line[4:].strip()
                current_data["description"] = description

        # Don't forget the last transaction!
        if current_data:
            transactions.append(UnifiedTransaction(**current_data))

        return transactions
