import os

# Tests must NEVER touch the real Supabase database, even if .env has DATABASE_URL.
# (load_dotenv doesn't override variables that are already set.)
os.environ["DATABASE_URL"] = ""
