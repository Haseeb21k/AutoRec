from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core import security, database
from app.models import tables

# This tells FastAPI where to find the token (in the Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(tables.User).filter(tables.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_superuser(
    current_user: tables.User = Depends(get_current_user),
):
    if current_user.role != "superuser":
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user