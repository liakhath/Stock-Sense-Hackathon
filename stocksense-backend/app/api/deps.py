from typing import Annotated, Optional

from fastapi import Depends, Header, Request

from app.engine import StockEngine


def get_engine(request: Request) -> StockEngine:
    return request.app.state.engine


def get_current_user(x_user: Optional[str] = Header(default=None)) -> str:
    """TEMPORARY until auth: the frontend sends the user's name in an `X-User` header.
    The auth step replaces this with JWT, and no route needs to change."""
    return (x_user or "").strip() or "anonymous"


Engine = Annotated[StockEngine, Depends(get_engine)]
CurrentUser = Annotated[str, Depends(get_current_user)]