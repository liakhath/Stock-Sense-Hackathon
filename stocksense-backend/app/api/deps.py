from typing import Annotated, Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.auth.security import decode_token
from app.auth.users import Account, UserRepo
from app.engine import StockEngine
from app.services.alerts import AlertCenter


def get_engine(request: Request) -> StockEngine:
    return request.app.state.engine


def get_alerts(request: Request) -> AlertCenter:
    return request.app.state.alerts


def get_users(request: Request) -> UserRepo:
    return request.app.state.users


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


def get_account(request: Request,
                authorization: Optional[str] = Header(default=None),
                x_user: Optional[str] = Header(default=None)) -> Account:
    """Who is calling?
    - AUTH_REQUIRED=true  (default): needs `Authorization: Bearer <token>` from /api/auth/login
    - AUTH_REQUIRED=false (legacy/dev): old `X-User` header, no role limits"""
    if not request.app.state.auth_required:
        name = (x_user or "").strip() or "anonymous"
        return Account(id=0, name=name, email=name, role="manager")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Not logged in")
    try:
        payload = decode_token(authorization[7:].strip(), request.app.state.jwt_secret)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Session expired, please log in again")
    except jwt.PyJWTError:
        raise _unauthorized("Invalid token, please log in again")

    acc = request.app.state.users.get(int(payload.get("sub", 0)))
    if acc is None or not acc.active:
        raise _unauthorized("Account not found or disabled")
    return acc


def get_current_user(account: Account = Depends(get_account)) -> str:
    """The identity string recorded on operations and the ledger (email when logged in)."""
    return account.email


def require_manager(account: Account = Depends(get_account)) -> Account:
    if not account.is_manager:
        raise HTTPException(403, "Only managers can do this")
    return account


Engine = Annotated[StockEngine, Depends(get_engine)]
Alerts = Annotated[AlertCenter, Depends(get_alerts)]
Users = Annotated[UserRepo, Depends(get_users)]
CurrentAccount = Annotated[Account, Depends(get_account)]
CurrentUser = Annotated[str, Depends(get_current_user)]
Manager = Annotated[Account, Depends(require_manager)]
