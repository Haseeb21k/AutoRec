from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

# --- TRANSACTION SCHEMAS ---
class TransactionBase(BaseModel):
    date: date
    amount: Decimal
    description: Optional[str] = None
    external_ref_id: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionOut(TransactionBase):
    id: str
    statement_id: str
    
    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy objects

# --- STATEMENT SCHEMAS ---
class StatementBase(BaseModel):
    filename: str
    bank_name: str

class StatementOut(StatementBase):
    id: str
    uploaded_at: datetime
    transactions: List[TransactionOut] = []

    class Config:
        from_attributes = True

class LedgerBase(BaseModel):
    date: date
    amount: Decimal
    description: Optional[str] = None
    gl_code: Optional[str] = None

class LedgerOut(LedgerBase):
    id: str
    
    class Config:
        from_attributes = True