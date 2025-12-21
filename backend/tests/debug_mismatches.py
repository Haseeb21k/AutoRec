from app.core.database import SessionLocal
from app.models import tables

def check_mismatches():
    db = SessionLocal()
    try:
        print("--- DB Debug: ReconciliationMatch ---")
        total = db.query(tables.ReconciliationMatch).count()
        print(f"Total Matches: {total}")
        
        by_type = {}
        matches = db.query(tables.ReconciliationMatch).all()
        for m in matches:
            t = m.match_type
            by_type[t] = by_type.get(t, 0) + 1
            
        print("Counts by Type:", by_type)
        
        mismatches = db.query(tables.ReconciliationMatch).filter(tables.ReconciliationMatch.match_type == 'mismatch').all()
        print(f"Mismatches found: {len(mismatches)}")
        
        print("\n--- Transaction Stats ---")
        total_tx = db.query(tables.Transaction).count()
        print(f"Total Transactions: {total_tx}")
        
        # Unmatched Transactions (should be 0 if mismatches are working and everything is processed)
        unmatched_tx_count = db.query(tables.Transaction).outerjoin(
            tables.ReconciliationMatch, tables.Transaction.id == tables.ReconciliationMatch.transaction_id
        ).filter(tables.ReconciliationMatch.id == None).count()
        print(f"Transactions without ANY match record: {unmatched_tx_count}")

    finally:
        db.close()

if __name__ == "__main__":
    check_mismatches()
