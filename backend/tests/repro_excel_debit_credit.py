import sys
import os
import pandas as pd
import io
from decimal import Decimal

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from parsers.csv_strategy import CSVStrategy

def test_excel_debit_credit():
    print("Testing Excel with Debit/Credit columns...")
    
    # 1. Create a DataFrame like the user's
    data = [
        {'Date': '2025-11-03', 'Description': 'Grocery', 'Ref': 'POS-1', 'Debit': 150.00, 'Credit': None},
        {'Date': '2025-11-05', 'Description': 'Salary', 'Ref': 'ACH-1', 'Debit': None, 'Credit': 3200.00},
    ]
    df = pd.DataFrame(data)
    
    # Save to bytes
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    content = output.getvalue()
    
    # 2. Try parsing with default "Amount" mapping
    parser = CSVStrategy()
    mapping = {'date': 'Date', 'amount': 'Amount', 'description': 'Description'}
    
    try:
        results = parser.parse(content, column_mapping=mapping)
        print("✅ Parsed successfully!")
        for tx in results:
            print(f"  {tx.date}: {tx.amount} ({tx.description})")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")

if __name__ == "__main__":
    # We need xlsxwriter to create the mock excel in memory
    # If not installed, we can just use the user provided 'excelgen.py' logic or installing it.
    try:
        import xlsxwriter
        test_excel_debit_credit()
    except ImportError:
        print("Skipping test generation: xlsxwriter not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "xlsxwriter"])
        test_excel_debit_credit()
