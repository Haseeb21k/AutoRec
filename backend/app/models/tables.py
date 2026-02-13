import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

# --- 1. USERS TABLE (UPDATED) ---
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    # Password is now nullable because invited users won't have one initially
    password_hash = Column(String, nullable=True) 
    role = Column(String, default="standard") # 'superuser', 'standard'
    is_active = Column(Boolean, default=True)
    
    # NEW: Token for verifying the invite link
    invite_token = Column(String, nullable=True)
    
    # Relationships
    uploads = relationship("BankStatement", back_populates="uploader")

# --- 2. BANK STATEMENTS (METADATA) ---
class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    bank_name = Column(String, nullable=False) 
    format_type = Column(String, nullable=False) 
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    uploaded_by = Column(String, ForeignKey("users.id"))
    
    uploader = relationship("User", back_populates="uploads")
    transactions = relationship("Transaction", back_populates="statement")

# --- 3. TRANSACTIONS (NORMALIZED DATA) ---
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String, nullable=True)
    external_ref_id = Column(String, nullable=True, index=True)
    raw_source = Column(String, nullable=True) 
    
    statement_id = Column(String, ForeignKey("bank_statements.id"))
    
    statement = relationship("BankStatement", back_populates="transactions")
    reconciliation_match = relationship("ReconciliationMatch", back_populates="transaction", uselist=False)

# --- 4. INTERNAL LEDGER ---
class InternalLedger(Base):
    __tablename__ = "internal_ledger"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String, nullable=True)
    gl_code = Column(String, nullable=True)
    
    reconciliation_match = relationship("ReconciliationMatch", back_populates="ledger", uselist=False)

# --- 5. RECONCILIATION MATCHES ---
class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    transaction_id = Column(String, ForeignKey("transactions.id"), unique=True)
    ledger_id = Column(String, ForeignKey("internal_ledger.id"), unique=True)
    
    match_type = Column(String)
    confidence_score = Column(Numeric(3, 2))
    matched_at = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("Transaction", back_populates="reconciliation_match")
    ledger = relationship("InternalLedger", back_populates="reconciliation_match")