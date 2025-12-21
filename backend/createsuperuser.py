import sys
import os

# --- PATH FIX ---
# This allows the script to find 'backend' even if you run it from inside the folder.
# It adds the parent directory (the root of your project) to Python's search path.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

# --- IMPORTS ---
# Run this from the directory containing 'app' (e.g., /app in Docker or backend/ locally)
from app.core.database import SessionLocal, engine, Base
from app.models import tables
from app.core.security import get_password_hash

def create_superuser():
    print("Checking database tables...")
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("\n--- Create Superuser ---")
    # Try getting from Env vars first (Non-interactive), else input
    email = os.getenv("SUPERUSER_EMAIL") or input("Enter Superuser Email: ")
    password = os.getenv("SUPERUSER_PASSWORD") or input("Enter Superuser Password: ")
    
    # Check if user exists
    existing = db.query(tables.User).filter(tables.User.email == email).first()
    if existing:
        print(f"❌ Error: User '{email}' already exists!")
        db.close()
        return

    # Create user
    try:
        print(f"DEBUG: Password received. Length: {len(password)}")
        print(f"DEBUG: First 2 chars: {password[:2]!r}")
    
        hash_value = get_password_hash(password)
    
        user = tables.User(
        email=email,
        password_hash=hash_value,
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