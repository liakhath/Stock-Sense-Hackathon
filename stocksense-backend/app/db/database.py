"""Database connection (Supabase Postgres in production, SQLite allowed for tests)."""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def normalize_url(url: str) -> str:
    """Supabase gives `postgresql://...`; tell SQLAlchemy to use the psycopg 3 driver."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def make_engine(url: str) -> Engine:
    url = normalize_url(url)
    kwargs = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        kwargs.update(
            pool_size=5,
            max_overflow=5,
            pool_recycle=300,
            # keeps it working with Supabase's pooler (no server-side prepared statements)
            connect_args={"prepare_threshold": None},
        )
    return create_engine(url, **kwargs)
