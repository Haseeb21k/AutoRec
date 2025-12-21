from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import tables
from app.api.v1.endpoints.statements import router as statements_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.ledger import router as ledger_router
from app.api.v1.endpoints.reconcile import router as reconcile_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router

# --- DATABASE INIT ---
# This line creates the tables in the database file if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Reconciliation Engine")

# --- CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(statements_router, prefix="/api/v1/statements", tags=["statements"])
app.include_router(ledger_router, prefix="/api/v1/ledger", tags=["ledger"])

app.include_router(
    reconcile_router,
    prefix="/api/v1/reconcile",
    tags=["reconcile"]
)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])