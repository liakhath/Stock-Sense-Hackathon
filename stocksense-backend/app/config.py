import os


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
    # Fill the app with demo data on startup (useful while there's no database).
    seed_demo_data = os.getenv("SEED_DEMO_DATA", "true").lower() in ("1", "true", "yes")


settings = Settings()