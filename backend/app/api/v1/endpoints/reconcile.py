from typing import List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.matching_engine import MatchingEngine
from app.api.v1.endpoints import deps
# Import tables to access them for deletion
from app.models import tables
from app.core.websocket import manager
from app.schemas import schemas

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    """
    Triggers reconciliation in the background. 
    Returns immediately so Nginx doesn't timeout.
    """
    try:
        engine = MatchingEngine(db)
        background_tasks.add_task(engine.run, websocket_manager=manager)
        return {"status": "started", "message": "Reconciliation started in background"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Returns stats for ACTIVE (unreconciled) data only.
    """
    total_bank = db.query(tables.Transaction).filter(tables.Transaction.report_id == None).count()
    total_matches = db.query(tables.ReconciliationMatch).filter(tables.ReconciliationMatch.report_id == None).count()
    
    rate = 0
    if total_bank > 0:
        rate = round((total_matches / total_bank) * 100, 1)
        
    return {
        "total_transactions": total_bank,
        "total_matches": total_matches,
        "reconciliation_rate": rate
    }

@router.delete("/clear")
async def clear_data(db: Session = Depends(get_db)):
    """
    Clears only UNRECONCILED data (data not part of a saved report).
    """
    try:
        # 1. Matches with no report_id
        db.query(tables.ReconciliationMatch).filter(tables.ReconciliationMatch.report_id == None).delete()
        
        # 2. Transactions with no report_id
        db.query(tables.Transaction).filter(tables.Transaction.report_id == None).delete()
        
        # 3. Ledger with no report_id
        db.query(tables.InternalLedger).filter(tables.InternalLedger.report_id == None).delete()
        
        db.commit()

        # Broadcast clear event to all connected clients (Dashboard)
        await manager.broadcast({"type": "clear"})

        return {"status": "success", "message": "Unreconciled data cleared"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: SAVE & HISTORY ENDPOINTS ---

@router.post("/save", response_model=schemas.ReportOut)
def save_reconciliation(
    report_in: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    """
    Finalizes the current matches into a saved report.
    """
    # 1. Get current matches (where report_id is NULL)
    active_matches = db.query(tables.ReconciliationMatch).filter(
        tables.ReconciliationMatch.report_id == None
    ).all()
    
    if not active_matches:
        raise HTTPException(status_code=400, detail="No active matches to save")
        
    # 2. Calculate summary stats
    total_tx = len(active_matches)
    matched_count = len([m for m in active_matches if m.match_type != 'mismatch'])
    total_amount = sum([m.transaction.amount for m in active_matches])
    
    # 3. Create Report
    report = tables.ReconciliationReport(
        name=report_in.name,
        created_by=current_user.id,
        total_transactions=total_tx,
        matched_count=matched_count,
        total_amount=total_amount
    )
    db.add(report)
    db.flush() # Get report.id
    
    # 4. Link matches, transactions, and ledgers to the report
    for match in active_matches:
        match.report_id = report.id
        if match.transaction:
            match.transaction.report_id = report.id
        if match.ledger:
            match.ledger.report_id = report.id
            
    db.commit()
    db.refresh(report)
    return report

@router.get("/reports", response_model=List[schemas.ReportOut])
def list_reports(db: Session = Depends(get_db)):
    return db.query(tables.ReconciliationReport).order_by(tables.ReconciliationReport.created_at.desc()).all()

@router.get("/reports/{report_id}")
def get_report_details(report_id: str, db: Session = Depends(get_db)):
    report = db.query(tables.ReconciliationReport).filter(tables.ReconciliationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Return report metadata + matches
    matches = []
    for m in report.matches:
        matches.append({
            "id": m.id,
            "match_type": m.match_type,
            "amount": m.transaction.amount,
            "date": m.transaction.date,
            "bank_desc": m.transaction.description,
            "ledger_desc": m.ledger.description if m.ledger else "-",
            "confidence": m.confidence_score
        })
        
    return {
        "metadata": {
            "id": report.id,
            "name": report.name,
            "created_at": report.created_at,
            "total_transactions": report.total_transactions,
            "matched_count": report.matched_count
        },
        "matches": matches
    }

@router.delete("/reports/{report_id}")
def delete_report(
    report_id: str, 
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    """
    Deletes a saved report and all associated finalized records.
    """
    report = db.query(tables.ReconciliationReport).filter(tables.ReconciliationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        # 1. Delete associated matches
        db.query(tables.ReconciliationMatch).filter(tables.ReconciliationMatch.report_id == report_id).delete()
        
        # 2. Delete associated transactions (they are finalized)
        db.query(tables.Transaction).filter(tables.Transaction.report_id == report_id).delete()
        
        # 3. Delete associated ledger entries
        db.query(tables.InternalLedger).filter(tables.InternalLedger.report_id == report_id).delete()
        
        # 4. Delete the report itself
        db.delete(report)
        
        db.commit()
        return {"status": "success", "message": "Report and associated data deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: RECENT ACTIVITY ENDPOINT ---
@router.get("/activity")
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """
    Returns the recent matches that are NOT part of a saved report.
    """
    # If limit is -1 or very large, we return all
    query = db.query(tables.ReconciliationMatch)\
        .filter(tables.ReconciliationMatch.report_id == None)\
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
            "confidence": m.confidence_score,
            "report_id": m.report_id
        })
    return activity