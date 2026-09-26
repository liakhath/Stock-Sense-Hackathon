import logging
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import get_account
from app.api.routes import alerts as alerts_routes
from app.api.routes import auth as auth_routes
from app.api.routes import dashboard, imports, ledger, operations, products, reports, warehouses
from app.api.seed import seed_demo
from app.auth.security import hash_password
from app.auth.users import SqlUserRepo, UserRepo
from app.config import settings
from app.db.repository import PersistentStore
from app.engine import (
    ApprovalRequired, InsufficientStock, InvalidOperation, NotFound, StockEngine, StockError,
)
from app.services.alerts import AlertCenter

log = logging.getLogger("stocksense")

ERROR_STATUS = {
    NotFound: 404,
    InvalidOperation: 400,
    ApprovalRequired: 403,
    InsufficientStock: 409,
}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Demo logins (created only when there are no users yet)
DEMO_USERS = [
    ("Marcus Vance", "manager@stocksense.demo", "manager", "demo1234"),
    ("Alex Rivers", "staff@stocksense.demo", "staff", "demo1234"),
]


def build_engine() -> StockEngine:
    """Supabase if DATABASE_URL is set, otherwise in-memory. Seeds demo data only when empty."""
    store = None
    if settings.database_url:
        try:
            store = PersistentStore(settings.database_url).load()
        except Exception as e:
            raise RuntimeError(
                "Could not connect to the database. Check DATABASE_URL in stocksense-backend/.env "
                "(use the Supabase *Session pooler* URI with your real password)."
            ) from e
    engine = StockEngine(store=store,
                         adjustment_approval_threshold=settings.adjustment_approval_threshold)
    if settings.seed_demo_data and not engine.store.products:
        seed_demo(engine)
        if store:
            store.save()
    return engine


def build_users(engine: StockEngine) -> UserRepo:
    """Users live in the same database as the stock data (or in memory without a DB)."""
    store = engine.store
    users = SqlUserRepo(store.db) if isinstance(store, PersistentStore) else UserRepo()
    if settings.seed_demo_data and users.count() == 0:
        for name, email, role, pw in DEMO_USERS:
            users.add(name, email, role, hash_password(pw))
    return users


def _save(engine: StockEngine) -> None:
    with engine._lock:          # don't save half-way through another request's change
        engine.store.save()


def create_app(engine: Optional[StockEngine] = None, users: Optional[UserRepo] = None,
               auth_required: Optional[bool] = None) -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.4.0")
    app.state.engine = engine or build_engine()
    app.state.alerts = AlertCenter()
    app.state.users = users or build_users(app.state.engine)
    app.state.auth_required = settings.auth_required if auth_required is None else auth_required
    app.state.jwt_secret = settings.jwt_secret or secrets.token_urlsafe(32)
    if not settings.jwt_secret:
        log.warning("JWT_SECRET not set: using a random secret, everyone is logged out on restart")

    # Save changes to the database after every write request.
    # Registered BEFORE CORS so CORS headers are also added to its error response.
    @app.middleware("http")
    async def persist_changes(request: Request, call_next):
        response = await call_next(request)
        eng = request.app.state.engine
        if request.method in WRITE_METHODS and isinstance(eng.store, PersistentStore):
            try:
                await run_in_threadpool(_save, eng)
            except Exception:
                log.exception("Database save failed")
                return JSONResponse(status_code=503, content={
                    "detail": "The change could not be saved to the database. Please try again.",
                    "code": "DatabaseError"})
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(StockError)
    async def stock_error_handler(request: Request, exc: StockError):
        return JSONResponse(
            status_code=ERROR_STATUS.get(type(exc), 400),
            content={"detail": str(exc), "code": type(exc).__name__},
        )

    # Every data route needs a logged-in user (or X-User in legacy mode)
    for r in (products.router, operations.router, ledger.router, dashboard.router,
              warehouses.router, imports.router, reports.router, alerts_routes.router):
        app.include_router(r, prefix="/api", dependencies=[Depends(get_account)])
    app.include_router(auth_routes.router, prefix="/api")      # login/signup/reset are public

    @app.get("/api/health", tags=["Health"])
    def health():
        storage = "database" if isinstance(app.state.engine.store, PersistentStore) else "memory"
        return {"status": "ok", "storage": storage, "auth_required": app.state.auth_required}

    return app


app = create_app()
