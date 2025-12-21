from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from decimal import Decimal

class UnifiedTransaction(BaseModel):
    """
    Standardized transaction model that all parsers must return.
    Serves as the Single Source of Truth for the Reconciliation Engine.
    """
    date: date
    amount: Decimal
    description: str
    external_ref_id: Optional[str] = None
    raw_source: Optional[str] = None
    
    # Metadata for the parser source
    source_format: str = Field(..., description="csv, excel, pdf, mt940")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator('amount')
    def amount_must_be_valid(cls, v):
        if v is None:
            raise ValueError('Amount cannot be None')
        return v

    class Config:
        frozen = True # Make it immutable
