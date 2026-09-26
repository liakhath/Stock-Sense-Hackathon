from typing import Annotated, Optional

from fastapi import Depends, Header, Request

from app.engine import StockEngine
from app.services.alerts import AlertCenter


def get_engine(request: Request) -> StockEngine:
    return request.app.state.engine


def get_alerts(request: Request) -> AlertCenter:
    return request.app.state.alerts


def get_current_user(x_user: Optional[str] = Header(default=None)) -> str:
    """TEMPORARY until auth: the frontend sends the user's name in an `X-User` header.
    The auth step replaces this with JWT, and no route needs to change."""
    return (x_user or "").strip() or "anonymous"


Engine = Annotated[StockEngine, Depends(get_engine)]
Alerts = Annotated[AlertCenter, Depends(get_alerts)]
CurrentUser = Annotated[str, Depends(get_current_user)]