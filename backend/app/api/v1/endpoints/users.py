from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.models import tables
from app.core import security
from app.api.v1.endpoints import deps
from app.core.email_utils import send_invite_email 

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    role: str = "standard"

class UserOut(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool

class PasswordSetup(BaseModel):
    token: str
    password: str

@router.get("/", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    return db.query(tables.User).all()

@router.post("/invite")
def invite_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    """
    Admin invites a user. Sends REAL email if configured.
    """
    existing = db.query(tables.User).filter(tables.User.email == user_in.email).first()
    if existing:
        raise HTTPException(400, "User already exists")

    invite_token = str(uuid.uuid4())

    user = tables.User(
        email=user_in.email,
        role=user_in.role,
        is_active=True,
        invite_token=invite_token,
        password_hash=None 
    )
    db.add(user)
    db.commit()

    # --- SEND EMAIL ---
    # This runs synchronously (might pause the server for 1-2s). 
    # In massive scale apps, use BackgroundTasks.
    send_invite_email(user_in.email, invite_token)

    return {"status": "invited", "email": user_in.email}

@router.patch("/{user_id}/status")
def toggle_status(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    user = db.query(tables.User).filter(tables.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    if user.id == current_user.id:
        raise HTTPException(400, "Cannot deactivate yourself")

    user.is_active = not user.is_active
    db.commit()
    return {"status": "updated", "is_active": user.is_active}

@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: tables.User = Depends(deps.get_current_superuser)
):
    """
    Permanently delete a user.
    """
    user = db.query(tables.User).filter(tables.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    if user.id == current_user.id:
        raise HTTPException(400, "Cannot delete yourself")

    try:
        db.delete(user)
        db.commit()
        return {"status": "success", "message": "User deleted"}
    except Exception:
        # If user has uploaded files, FK constraints might block deletion.
        # For V1, we block deletion if they have data.
        raise HTTPException(400, "Cannot delete user. They may have linked data (uploads).")

@router.post("/setup-password")
def setup_password(
    payload: PasswordSetup,
    db: Session = Depends(get_db)
):
    user = db.query(tables.User).filter(tables.User.invite_token == payload.token).first()
    if not user:
        raise HTTPException(400, "Invalid or expired token")

    user.password_hash = security.get_password_hash(payload.password)
    user.invite_token = None 
    db.commit()

    return {"status": "success", "message": "Password set successfully"}