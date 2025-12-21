import csv
import random
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOTAL_TRANSACTIONS = 1000
START_DATE = datetime(2023, 1, 1)
OUTPUT_BANK = "bank_statement.csv"
OUTPUT_LEDGER = "ledger_export.csv"

# --- GENERATORS ---
def random_date(start, end_days=365):
    return start + timedelta(days=random.randint(0, end_days))

VENDORS = ["AWS", "Slack", "Office Depot", "WeWork", "Uber", "Delta Air", "Google Ads"]
CLIENTS = ["Acme Corp", "Globex", "Stark Ind", "Wayne Ent", "Cyberdyne", "Umbrella Corp"]

# --- LOGIC ---
bank_rows = [["Date", "Amount", "Description"]]
ledger_rows = [["Date", "Amount", "Description", "GL Code"]]

print(f"🚀 Generating {TOTAL_TRANSACTIONS} transactions...")

for i in range(TOTAL_TRANSACTIONS):
    base_date = random_date(START_DATE)
    
    # Scenario 1: Expense (Vendor Payment)
    # 60% chance of expense
    if random.random() < 0.6:
        vendor = random.choice(VENDORS)
        amount = round(random.uniform(50.00, 5000.00), 2)
        
        # Bank side: Negative, Date might be delayed 1-3 days
        bank_date = base_date + timedelta(days=random.randint(0, 3))
        bank_desc = f"POS DEBIT {vendor} #8832"
        bank_amount = -amount # Bank shows debit as negative
        
        # Ledger side: Positive (Accounting view), Exact Date
        ledger_date = base_date
        ledger_desc = f"Payment to {vendor}"
        ledger_amount = amount # Ledger often shows absolute value
        gl_code = "5000-EXP"

    # Scenario 2: Income (Client Payment)
    else:
        client = random.choice(CLIENTS)
        amount = round(random.uniform(2000.00, 50000.00), 2)
        
        # Bank side: Positive
        bank_date = base_date + timedelta(days=random.randint(0, 5)) # Checks take longer
        bank_desc = f"WIRE DEPOSIT FROM {client}"
        bank_amount = amount
        
        # Ledger side: Positive
        ledger_date = base_date
        ledger_desc = f"Inv #{random.randint(1000,9999)} - {client}"
        ledger_amount = amount
        gl_code = "4000-REV"

    # --- INTRODUCE NOISE (The "Real World" Factor) ---
    rand_val = random.random()
    
    if rand_val < 0.05: 
        # 5% Chance: Exists in Ledger ONLY (Uncleared check)
        ledger_rows.append([ledger_date.strftime("%Y-%m-%d"), ledger_amount, ledger_desc, gl_code])
    elif rand_val < 0.10:
        # 5% Chance: Exists in Bank ONLY (Bank Fee or Mystery Charge)
        bank_rows.append([bank_date.strftime("%Y-%m-%d"), bank_amount, bank_desc])
    else:
        # 90% Chance: It matches (Perfectly or Fuzzy)
        bank_rows.append([bank_date.strftime("%Y-%m-%d"), bank_amount, bank_desc])
        ledger_rows.append([ledger_date.strftime("%Y-%m-%d"), ledger_amount, ledger_desc, gl_code])

# --- WRITE FILES ---
with open(OUTPUT_BANK, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(bank_rows)

with open(OUTPUT_LEDGER, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(ledger_rows)

print(f"✅ Done! Generated '{OUTPUT_BANK}' and '{OUTPUT_LEDGER}'")
print(f"   - Bank Rows: {len(bank_rows)}")
print(f"   - Ledger Rows: {len(ledger_rows)}")