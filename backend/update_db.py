from sqlalchemy import create_engine, text
import os

db_path = os.path.join(os.getcwd(), "financial_system.db")
engine = create_engine(f"sqlite:///{db_path}")

print("Updating database schema...")

with engine.connect() as conn:
    # Add report_id columns
    tables_to_update = ["transactions", "internal_ledger", "reconciliation_matches"]
    for table in tables_to_update:
        try:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN report_id VARCHAR"))
            print(f"Added report_id to {table}")
        except Exception as e:
            print(f"Could not add to {table} (probably already exists): {e}")
    
    conn.commit()

# Also trigger table creation for the new report table
from app.core.database import Base
from app.models import tables
Base.metadata.create_all(bind=engine)
print("Schema update complete.")
