from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import tables
from app.core import security

router = APIRouter()

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    remember_me: bool = Form(False),
    db: Session = Depends(get_db)
):
    # 1. Find User
    user = db.query(tables.User).filter(tables.User.email == form_data.username).first()
    
    # 2. Verify Password
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Create Token
    # Default to 8 hours (workday) if not remembered, 30 days if remembered
    expiry = timedelta(days=30) if remember_me else timedelta(hours=8)
    
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=expiry
    )
    
    return {"access_token": access_token, "token_type": "bearer"}