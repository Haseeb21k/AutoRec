from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# Default to SQLite if DATABASE_URL not set
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./financial_system.db")

# Fix for Railway/Heroku: SQLAlchemy 1.4+ requires 'postgresql://', but some providers give 'postgres://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# --- ENGINE ---
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

# --- SESSION ---
# This is the "database session factory" we will use in our API
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- BASE ---
# All our models will inherit from this class
Base = declarative_base()

def get_db():
    """
    Dependency function to yield a database session for a request
    and close it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()