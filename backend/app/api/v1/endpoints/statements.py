from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import tables
from app.schemas import schemas
from app.api.v1.endpoints import deps

# Import our parsers
from parsers.csv_strategy import CSVStrategy
from parsers.mt940_strategy import MT940Strategy

router = APIRouter()

@router.get("/", response_model=List[schemas.StatementOut])
def read_statements(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all uploaded statements.
    """
    statements = db.query(tables.BankStatement).offset(skip).limit(limit).all()
    return statements

@router.post("/upload", response_model=schemas.StatementOut)
async def upload_statement(
    file: UploadFile = File(...),
    bank_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    """
    Uploads a bank statement (CSV/Excel/MT940/PDF), parses it via NormalizationService, and saves to DB.
    """
    from app.services.normalization_service import NormalizationService

    # 1. Normalize File
    unified_transactions = await NormalizationService.normalize_file(file)
    
    # 2. Save Statement Metadata to DB
    # We infer format from the first transaction or file extension
    format_type = unified_transactions[0].source_format if unified_transactions else "unknown"
    
    db_statement = tables.BankStatement(
        filename=file.filename,
        bank_name=bank_name,
        format_type=format_type
    )
    db.add(db_statement)
    db.commit()
    db.refresh(db_statement)

    # 3. Save Transactions to DB
    for tx in unified_transactions:
        db_tx = tables.Transaction(
            date=tx.date,
            amount=tx.amount,
            description=tx.description,
            external_ref_id=tx.external_ref_id,
            raw_source=tx.raw_source,
            statement_id=db_statement.id
        )
        db.add(db_tx)
    
    db.commit()
    db.refresh(db_statement)
    
    return db_statement

@router.delete("/reset", status_code=204)
def reset_data(db: Session = Depends(get_db)):
    """
    DANGER: Deletes ALL statements, transactions, and matches.
    """
    # 1. Delete Matches (Child of Transaction)
    db.query(tables.ReconciliationMatch).delete()
    
    # 2. Delete Transactions (Child of Statement)
    db.query(tables.Transaction).delete()
    
    # 3. Delete Statements
    db.query(tables.BankStatement).delete()
    
    db.commit()
    return None