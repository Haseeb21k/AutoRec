from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import tables
from app.schemas import schemas
from app.api.v1.endpoints import deps
from parsers.csv_strategy import CSVStrategy

router = APIRouter()

@router.post("/upload", response_model=List[schemas.LedgerOut])
async def upload_ledger(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    """
    Uploads an Internal Ledger file (CSV/Excel/MT940/PDF) and saves it.
    """
    from app.services.normalization_service import NormalizationService

    # 1. Normalize File
    # For ledger, we might want different defaults, but mostly 'amount' and 'date' are standard.
    try:
        data = await NormalizationService.normalize_file(file)
    except Exception as e:
         raise HTTPException(400, f"Parsing error: {str(e)}")

    # 2. Save to DB
    saved_records = []
    for row in data:
        db_ledger = tables.InternalLedger(
            date=row.date,
            amount=row.amount,
            description=row.description,
            gl_code=getattr(row, 'external_ref_id', 'GL-000') or 'GL-000'
        )
        db.add(db_ledger)
        saved_records.append(db_ledger)
    
    db.commit()
    
    # Refresh all to get IDs
    for record in saved_records:
        db.refresh(record)
        
    return saved_records

@router.get("/", response_model=List[schemas.LedgerOut])
def get_ledger(db: Session = Depends(get_db)):
    return db.query(tables.InternalLedger).all()