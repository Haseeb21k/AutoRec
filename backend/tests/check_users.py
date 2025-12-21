from app.core.database import SessionLocal
from app.models.tables import User

def check_users():
    db = SessionLocal()
    try:
        count = db.query(User).count()
        print(f"Total Users in Database: {count}")
        
        # Optional: Print emails to verify
        users = db.query(User).all()
        for u in users:
            print(f" - {u.email} (Role: {u.role})")
            
    except Exception as e:
        print(f"Error querying users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
