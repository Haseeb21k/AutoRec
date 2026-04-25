from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import timedelta
from decimal import Decimal
from app.models import tables

class MatchingEngine:
    def __init__(self, db: Session):
        self.db = db

    async def run(self, websocket_manager=None):
        """
        Executes the reconciliation logic in passes, optimized for large datasets.
        """
        import asyncio 

        results = {
            "bank_items_scanned": 0,
            "ledger_items_scanned": 0,
            "exact_matches": 0,
            "fuzzy_matches": 0
        }

        # 1. Fetch all UNMATCHED Bank Transactions
        unmatched_bank = self.db.query(tables.Transaction).outerjoin(
            tables.ReconciliationMatch, tables.Transaction.id == tables.ReconciliationMatch.transaction_id
        ).filter(tables.ReconciliationMatch.id == None).all()

        # 2. Fetch all UNMATCHED Ledger Entries
        unmatched_ledger = self.db.query(tables.InternalLedger).outerjoin(
            tables.ReconciliationMatch, tables.InternalLedger.id == tables.ReconciliationMatch.ledger_id
        ).filter(tables.ReconciliationMatch.id == None).all()

        results["bank_items_scanned"] = len(unmatched_bank)
        results["ledger_items_scanned"] = len(unmatched_ledger)

        if not unmatched_bank:
            return results
        
        # --- OPTIMIZATION: Index ledger entries by amount for O(1) lookup ---
        ledger_index = {}
        for l in unmatched_ledger:
            amt = l.amount
            if amt not in ledger_index: ledger_index[amt] = []
            ledger_index[amt].append(l)
            
            # Also index flipped amount if different (for sign-flipped matches)
            flipped = -amt
            if flipped != amt:
                if flipped not in ledger_index: ledger_index[flipped] = []
                ledger_index[flipped].append(l)

        # Track which items are already matched to avoid double matching
        matched_bank_ids = set()
        matched_ledger_ids = set()
        
        # Helper to broadcast
        async def broadcast_match(match_obj):
            if websocket_manager:
                await websocket_manager.broadcast({
                    "id": match_obj.id,
                    "match_type": match_obj.match_type,
                    "amount": float(match_obj.transaction.amount),
                    "date": str(match_obj.transaction.date),
                    "bank_desc": match_obj.transaction.description,
                    "ledger_desc": match_obj.ledger.description if match_obj.ledger else "-",
                    "confidence": float(match_obj.confidence_score)
                })

        # --- PASS 1: EXACT MATCH (Amount + Date) ---
        for bank_tx in unmatched_bank:
            amt = bank_tx.amount
            candidates = ledger_index.get(amt, [])
            
            # Find candidate with exact date
            match = next((l for l in candidates if l.date == bank_tx.date and l.id not in matched_ledger_ids), None)
            
            if match:
                db_match = self._create_match(bank_tx, match, "exact", 1.0, commit=False)
                matched_bank_ids.add(bank_tx.id)
                matched_ledger_ids.add(match.id)
                results["exact_matches"] += 1
                await broadcast_match(db_match)

        self.db.commit() # Batch commit Pass 1

        # --- PASS 2: FUZZY DATE (Amount + Date +/- 2 Days) ---
        remaining_bank = [b for b in unmatched_bank if b.id not in matched_bank_ids]

        for bank_tx in remaining_bank:
            amt = bank_tx.amount
            candidates = ledger_index.get(amt, [])
            
            # Find candidate with date within 2 days
            match = next((
                l for l in candidates 
                if l.id not in matched_ledger_ids and abs((l.date - bank_tx.date).days) <= 2
            ), None)

            if match:
                db_match = self._create_match(bank_tx, match, "fuzzy_date", 0.85, commit=False)
                matched_bank_ids.add(bank_tx.id)
                matched_ledger_ids.add(match.id)
                results["fuzzy_matches"] += 1
                await broadcast_match(db_match)

        self.db.commit() # Batch commit Pass 2

        # --- FINAL PASS: REPORT MISMATCHES ---
        final_unmatched = [b for b in unmatched_bank if b.id not in matched_bank_ids]
        
        for tx in final_unmatched:
            db_match = self._create_match(tx, None, "mismatch", 0.0, commit=False)
            await broadcast_match(db_match)
        
        self.db.commit() # Batch commit Final Pass

        # Send completion event
        if websocket_manager:
            await websocket_manager.broadcast({
                "type": "complete",
                "results": results
            })

        return results

    def _create_match(self, bank_tx, ledger_tx, match_type, confidence, commit=True):
        """
        Helper to create match. Optionally batches commits for speed.
        """
        db_match = tables.ReconciliationMatch(
            transaction_id=bank_tx.id,
            ledger_id=ledger_tx.id if ledger_tx else None,
            match_type=match_type,
            confidence_score=confidence
        )
        self.db.add(db_match)
        
        # Link in memory
        bank_tx.reconciliation_match = db_match
        if ledger_tx:
            ledger_tx.reconciliation_match = db_match
        
        if commit:
            self.db.commit()
            self.db.refresh(db_match)
            
        return db_match