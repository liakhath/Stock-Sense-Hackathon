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

    # ---- Auth ----
    # true  = every /api route needs a login token (Authorization: Bearer ...)
    # false = legacy dev mode: old X-User header, no role limits (use only until the frontend has login)
    auth_required = os.getenv("AUTH_REQUIRED", "true").lower() in ("1", "true", "yes")
    # Secret used to sign login tokens. SET THIS in .env, otherwise everyone is logged out on restart.
    jwt_secret = os.getenv("JWT_SECRET", "").strip() or None
    jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))       # 12 hours
    # true = forgot-password response includes the code (for demos without email)
    otp_demo_mode = os.getenv("OTP_DEMO_MODE", "true").lower() in ("1", "true", "yes")
    # Optional email delivery for reset codes (e.g. Gmail: smtp.gmail.com / 587 / app password)
    smtp_host = os.getenv("SMTP_HOST", "").strip() or None
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip() or None
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM", "").strip() or None


settings = Settings()
