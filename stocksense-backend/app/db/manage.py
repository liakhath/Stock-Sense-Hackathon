"""Database commands. Run from stocksense-backend/:

    python -m app.db.manage status   -> show row counts
    python -m app.db.manage reset    -> DELETE ALL DATA and recreate empty tables
                                        (demo data is re-seeded on the next server start)
"""
import sys

from sqlalchemy import func, select

from app.config import settings
from app.db import tables as t
from app.db.repository import PersistentStore


def main() -> None:
    if not settings.database_url:
        sys.exit("DATABASE_URL is not set (put it in stocksense-backend/.env)")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    store = PersistentStore(settings.database_url)

    if cmd == "reset":
        if input("This deletes ALL StockSense data in the database. Type 'yes' to continue: ") != "yes":
            sys.exit("Cancelled.")
        store.drop_schema()
        store.create_schema()
        print("Database reset. Start the server to re-seed demo data.")
    elif cmd == "status":
        store.create_schema()
        with store.db.connect() as c:
            for table in t.metadata.sorted_tables:
                n = c.execute(select(func.count()).select_from(table)).scalar()
                print(f"{table.name:<16} {n} rows")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
