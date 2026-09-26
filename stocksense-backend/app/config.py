import os

try:  # read stocksense-backend/.env (DATABASE_URL etc.)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings:
    app_name = "StockSense API"
    cors_origins = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
        if o.strip()
    ]
    # Adjustments changing stock by more than this many units need a manager's approval.
    # Empty value = approvals off.
    adjustment_approval_threshold = os.getenv("ADJUSTMENT_APPROVAL_THRESHOLD", "10").strip() or None
    # Seed demo data when the store is EMPTY (first run on a fresh database, or no database).
    seed_demo_data = os.getenv("SEED_DEMO_DATA", "true").lower() in ("1", "true", "yes")
    # Supabase connection string. Empty = in-memory only (data lost on restart).
    database_url = os.getenv("DATABASE_URL", "").strip() or None


settings = Settings()
