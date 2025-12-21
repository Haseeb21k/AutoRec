import sys
import os

# --- PATH FIX ---
# This allows the script to find 'backend' even if you run it from inside the folder.
# It adds the parent directory (the root of your project) to Python's search path.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models import tables
from backend.app.core.security import get_password_hash

def create_superuser():
    print("Checking database tables...")
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("\n--- Create Superuser ---")
    email = input("Enter Superuser Email: ")
    password = input("Enter Superuser Password: ")
    
    # Check if user exists
    existing = db.query(tables.User).filter(tables.User.email == email).first()
    if existing:
        print(f"❌ Error: User '{email}' already exists!")
        db.close()
        return

    # Create user
    try:
        user = tables.User(
            email=email,
            password_hash=get_password_hash(password),
            role="superuser",
            is_active=True
        )
        
        db.add(user)
        db.commit()
        print(f"✅ Success! Superuser '{email}' created successfully.")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()