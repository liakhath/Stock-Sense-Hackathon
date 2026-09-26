import os

# Tests must NEVER touch the real Supabase database, even if .env has DATABASE_URL.
# (load_dotenv doesn't override variables that are already set.)
os.environ["DATABASE_URL"] = ""
# Older tests use the legacy X-User header; auth tests turn auth on explicitly.
os.environ["AUTH_REQUIRED"] = "false"
os.environ["OTP_DEMO_MODE"] = "true"
os.environ["SMTP_HOST"] = ""
