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
        Executes the reconciliation logic in passes.
        Optimized for performance with batched commits and reduced broadcasts.
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

        # Stop if we don't have data to process
        if not unmatched_bank:
            return results
        
        # Note: We continue even if unmatched_ledger is empty, 
        # because we still need to process unmatched_bank items as 'mismatches' in the final pass.

        # Convert ledger list to a mutable list so we can remove items as we match them
        available_ledger = list(unmatched_ledger)
        
        # Batching for performance
        pending_matches = []
        broadcast_counter = 0
        BROADCAST_EVERY = 2  # Broadcast every 2nd match - good balance of UX vs performance
        BATCH_SIZE = 100  # Commit every 100 matches
        
        # Helper to broadcast (now called selectively)
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
                # Small delay only when broadcasting for visual smoothness
                await asyncio.sleep(0.015)  # 15ms - barely noticeable but prevents flooding

        # Helper to commit batches
        def commit_batch():
            if pending_matches:
                try:
                    self.db.commit()
                    # Refresh all matches to get IDs
                    for match in pending_matches:
                        self.db.refresh(match)
                    print(f"✅ Committed batch of {len(pending_matches)} matches")
                    pending_matches.clear()
                except Exception as e:
                    print(f"❌ ERROR committing batch: {e}")
                    self.db.rollback()
                    pending_matches.clear()
                    raise  # Re-raise to stop reconciliation on error

        # --- PASS 1: EXACT MATCH (Amount + Date) ---
        for bank_tx in unmatched_bank:
            # Try to find a match. We check:
            # 1. Exact amount match
            # 2. FLIPPED sign match (e.g. -100 vs 100)
            match = next((
                l for l in available_ledger 
                if (l.amount == bank_tx.amount or l.amount == -bank_tx.amount) 
                and l.date == bank_tx.date
            ), None)
            
            if match:
                db_match = self._create_match_no_commit(bank_tx, match, "exact", 1.0)
                pending_matches.append(db_match)
                available_ledger.remove(match) 
                results["exact_matches"] += 1
                
                # Broadcast every Nth match
                broadcast_counter += 1
                if broadcast_counter % BROADCAST_EVERY == 0:
                    await broadcast_match(db_match)
                
                # Commit in batches
                if len(pending_matches) >= BATCH_SIZE:
                    commit_batch()
                continue 

        # Commit any remaining from Pass 1
        commit_batch()

        # --- PASS 2: FUZZY DATE (Amount + Date +/- 2 Days) ---
        # We filter again to get only bank items that were NOT matched in Pass 1
        remaining_bank = [b for b in unmatched_bank if not b.reconciliation_match]

        for bank_tx in remaining_bank:
            # Logic: Amount match AND Date difference <= 2 days
            match = next((
                l for l in available_ledger 
                if (l.amount == bank_tx.amount or l.amount == -bank_tx.amount)
                and abs((l.date - bank_tx.date).days) <= 2
            ), None)

            if match:
                db_match = self._create_match_no_commit(bank_tx, match, "fuzzy_date", 0.85)
                pending_matches.append(db_match)
                available_ledger.remove(match)
                results["fuzzy_matches"] += 1
                
                broadcast_counter += 1
                if broadcast_counter % BROADCAST_EVERY == 0:
                    await broadcast_match(db_match)
                
                if len(pending_matches) >= BATCH_SIZE:
                    commit_batch()

        # Commit any remaining from Pass 2
        commit_batch()

        # --- FINAL PASS: REPORT MISMATCHES ---
        # Any bank transaction that is still unmatched is a deviation
        final_unmatched = [b for b in unmatched_bank if not b.reconciliation_match]
        
        for tx in final_unmatched:
            db_match = self._create_match_no_commit(tx, None, "mismatch", 0.0)
            pending_matches.append(db_match)
            
            broadcast_counter += 1
            if broadcast_counter % BROADCAST_EVERY == 0:
                if websocket_manager:
                    await websocket_manager.broadcast({
                        "id": db_match.id,
                        "match_type": "mismatch",
                        "amount": float(tx.amount),
                        "date": str(tx.date),
                        "bank_desc": tx.description,
                        "ledger_desc": "-",
                        "confidence": 0.0
                    })
            
            if len(pending_matches) >= BATCH_SIZE:
                commit_batch()

        # Final commit for any remaining
        commit_batch()

        return results

    def _create_match_no_commit(self, bank_tx, ledger_tx, match_type, confidence):
        """
        Helper to create match WITHOUT committing (for batching).
        """
        db_match = tables.ReconciliationMatch(
            transaction_id=bank_tx.id,
            ledger_id=ledger_tx.id if ledger_tx else None,
            match_type=match_type,
            confidence_score=confidence
        )
        self.db.add(db_match)
        
        # Update objects in memory so our loops know they are taken
        bank_tx.reconciliation_match = db_match
        if ledger_tx:
            ledger_tx.reconciliation_match = db_match
        
        return db_match

    def _create_match(self, bank_tx, ledger_tx, match_type, confidence):
        """
        Legacy helper - creates and commits immediately.
        Kept for backwards compatibility but not used in optimized path.
        """
        db_match = tables.ReconciliationMatch(
            transaction_id=bank_tx.id,
            ledger_id=ledger_tx.id if ledger_tx else None,
            match_type=match_type,
            confidence_score=confidence
        )
        self.db.add(db_match)
        
        # We also update the objects in memory so our loops know they are taken
        bank_tx.reconciliation_match = db_match
        if ledger_tx:
            ledger_tx.reconciliation_match = db_match
        
        self.db.commit()
        self.db.refresh(db_match) # Refresh to get IDs etc
        return db_match