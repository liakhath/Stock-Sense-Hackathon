from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import alerts as alerts_routes
from app.api.routes import dashboard, imports, ledger, operations, products, reports, warehouses
from app.config import settings
from app.engine import (
    ApprovalRequired, InsufficientStock, InvalidOperation, NotFound, StockEngine, StockError,
)
from app.api.seed import seed_demo
from app.services.alerts import AlertCenter

ERROR_STATUS = {
    NotFound: 404,
    InvalidOperation: 400,
    ApprovalRequired: 403,
    InsufficientStock: 409,
}


def create_app(engine: Optional[StockEngine] = None) -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.2.0")

    if engine is None:
        engine = StockEngine(adjustment_approval_threshold=settings.adjustment_approval_threshold)
        if settings.seed_demo_data:
            seed_demo(engine)
    app.state.engine = engine
    app.state.alerts = AlertCenter()

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

    for r in (products.router, operations.router, ledger.router, dashboard.router,
              warehouses.router, imports.router, reports.router, alerts_routes.router):
        app.include_router(r, prefix="/api")

    @app.get("/api/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()