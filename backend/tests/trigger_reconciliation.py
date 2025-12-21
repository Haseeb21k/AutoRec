from app.core.database import SessionLocal
from app.services.matching_engine import MatchingEngine
import asyncio

async def run_manual_reconcile():
    db = SessionLocal()
    try:
        print("Starting Manual Reconciliation Trigger...")
        engine = MatchingEngine(db)
        # We pass None for websocket manager since we just want to test DB persistence logic
        results = await engine.run(websocket_manager=None)
        print("Reconciliation Finished!")
        print(f"Results: {results}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_manual_reconcile())
