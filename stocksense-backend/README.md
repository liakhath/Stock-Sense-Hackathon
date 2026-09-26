# StockSense Backend

FastAPI backend for StockSense.
See the [root README](../README.md) for the full project description, quick-start guide,
demo accounts, and API overview.

---

## Setup

```bash
python -m pip install -r requirements.txt
copy .env.example .env   # then edit .env
python -m uvicorn app.main:app --port 8000
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No | Supabase Session pooler URI. Empty = in-memory |
| `JWT_SECRET` | **Yes** | Long random string (generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`) |
| `AUTH_REQUIRED` | No | Default `true`. Set `false` only for quick local testing without a login form |
| `JWT_EXPIRE_MINUTES` | No | Default `720` (12 hours) |
| `ADJUSTMENT_APPROVAL_THRESHOLD` | No | Default `10`. Adjustments above this unit count need manager approval |
| `OTP_DEMO_MODE` | No | Default `true`. Returns the 6-digit reset code in the API response |
| `SEED_DEMO_DATA` | No | Default `true`. Seeds products and two demo users on a fresh/empty store |
| `SMTP_*` | No | Configure to email OTP codes instead of returning them |

See `.env.example` for the full list with comments.

---

## Database

```bash
# Create/verify schema and show row counts
python -m app.db.manage status

# Wipe all data and re-create empty tables
python -m app.db.manage reset
```

Tables are created automatically on the first `status` or server start.
Demo data (5 products, 2 warehouses, 2 users) is seeded when the store is empty.

---

## Tests

```bash
python -m pytest -q
# Expected: 43 passed
```

Database tests (`test_db.py`) are skipped when `DATABASE_URL` is not set.

---

## Interactive API docs

Start the server, then open: `http://localhost:8000/docs`

All endpoints, request/response schemas, and authentication requirements are documented there.

---

## Architecture notes

- **`app/engine/stock_engine.py`** — single source of truth for all stock state.
  Every receipt, delivery, transfer, and adjustment goes through `StockEngine`.
  Thread-safe via a single `RLock`; all writes are atomic.

- **`app/db/repository.py`** — `PersistentStore` wraps SQLAlchemy; serialises the
  in-memory engine state to PostgreSQL after every write request (middleware in `main.py`).

- **`app/auth/`** — `SqlUserRepo` stores users in the same database.
  `security.py` handles bcrypt hashing and JWT creation/verification.

- **`app/services/`** — `AlertCenter` (stateful, per-process), CSV/Excel importer,
  analytics (valuation, movers).
