import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

raw_url = os.environ.get("DATABASE_URL", "")
url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

if not url:
    print("DATABASE_URL is not set in environment or .env file.")
else:
    engine = create_engine(url)

    with engine.connect() as conn:
        version = conn.execute(text("select version()")).scalar()
        print("Connected! ->", version[:60])
