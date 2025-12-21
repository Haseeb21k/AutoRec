from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.matching_engine import MatchingEngine
from app.api.v1.endpoints import deps
# Import tables to access them for deletion
from app.models import tables
from app.core.websocket import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive, or listen for commands if needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/run")
async def run_reconciliation(
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    try:
        engine = MatchingEngine(db)
        # Inject the global manager
        results = await engine.run(websocket_manager=manager)
        return {"status": "success", "results": results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_bank = db.query(tables.Transaction).count()
    total_matches = db.query(tables.ReconciliationMatch).count()
    
    rate = 0
    if total_bank > 0:
        rate = round((total_matches / total_bank) * 100, 1)
        
    return {
        "total_transactions": total_bank,
        "total_matches": total_matches,
        "reconciliation_rate": rate
    }

@router.delete("/clear")
def clear_data(db: Session = Depends(get_db)):
    try:
        db.query(tables.ReconciliationMatch).delete()
        db.query(tables.Transaction).delete()
        db.query(tables.InternalLedger).delete()
        db.query(tables.BankStatement).delete()
        db.commit()
        return {"status": "success", "message": "All data cleared"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: RECENT ACTIVITY ENDPOINT ---
@router.get("/activity")
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """
    Returns the recent matches with details.
    """
    # If limit is -1 or very large, we return all
    query = db.query(tables.ReconciliationMatch)\
        .order_by(tables.ReconciliationMatch.matched_at.desc())
        
    if limit > 0:
        query = query.limit(limit)
        
    matches = query.all()
    
    activity = []
    for m in matches:
        # Safety check for transaction (should exist)
        if not m.transaction:
            continue
            
        activity.append({
            "id": m.id,
            "match_type": m.match_type,
            "amount": m.transaction.amount,
            "date": m.transaction.date,
            "bank_desc": m.transaction.description,
            "ledger_desc": m.ledger.description if m.ledger else "-",
            "confidence": m.confidence_score
        })
    return activity