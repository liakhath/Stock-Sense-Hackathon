from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import CurrentAccount, Manager, Users
from app.auth import otp
from app.auth.security import create_token, hash_password, password_problem, verify_password
from app.auth.users import Account
from app.config import settings
from app.schemas.auth import (
    ChangePasswordIn, ForgotPasswordIn, ForgotPasswordOut, LoginIn, MessageOut, ResetPasswordIn,
    SignupIn, TokenOut, UserCreateIn, UserOut, UserUpdateIn,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
RESET_MSG = "If that email is registered, a 6-digit code has been sent. It expires in 10 minutes."


def _check_password(pw: str) -> None:
    problem = password_problem(pw)
    if problem:
        raise HTTPException(400, problem)


def _token_for(request: Request, acc: Account) -> TokenOut:
    minutes = settings.jwt_expire_minutes
    token = create_token(acc.id, acc.email, acc.role, request.app.state.jwt_secret, minutes)
    return TokenOut(access_token=token, expires_in=minutes * 60, user=UserOut.model_validate(acc))


# ---------------------------------------------------------------- public
@router.post("/signup", response_model=TokenOut, status_code=201)
def signup(body: SignupIn, request: Request, users: Users):
    """Self-signup creates a STAFF account (the very first user becomes manager).
    Managers are created by other managers via POST /auth/users."""
    if users.get_by_email(body.email):
        raise HTTPException(400, "An account with this email already exists")
    _check_password(body.password)
    role = "manager" if users.count() == 0 else "staff"
    acc = users.add(body.name, body.email, role, hash_password(body.password))
    return _token_for(request, acc)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, users: Users):
    acc = users.get_by_email(body.email)
    if acc is None or not verify_password(body.password, acc.password_hash):
        raise HTTPException(401, "Wrong email or password")
    if not acc.active:
        raise HTTPException(403, "This account is disabled. Ask a manager.")
    return _token_for(request, acc)


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(body: ForgotPasswordIn, request: Request, users: Users):
    """Always returns the same message (doesn't reveal whether the email exists)."""
    acc = users.get_by_email(body.email)
    if acc is None or not acc.active:
        return ForgotPasswordOut(message=RESET_MSG)
    code = otp.new_code()
    acc.reset_code_hash = otp.hash_code(code, request.app.state.jwt_secret)
    acc.reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=otp.OTP_TTL_MINUTES)
    acc.reset_attempts = 0
    users.save(acc)
    otp.send_code(acc.email, code, settings)
    return ForgotPasswordOut(message=RESET_MSG,
                             demo_code=code if settings.otp_demo_mode else None)


@router.post("/reset-password", response_model=MessageOut)
def reset_password(body: ResetPasswordIn, request: Request, users: Users):
    acc = users.get_by_email(body.email)
    invalid = HTTPException(400, "Invalid or expired code")
    if acc is None or not acc.reset_code_hash or acc.reset_expires_at is None:
        raise invalid
    if acc.reset_expires_at < datetime.now(timezone.utc) or acc.reset_attempts >= otp.OTP_MAX_ATTEMPTS:
        acc.reset_code_hash = None
        users.save(acc)
        raise HTTPException(400, "Code expired or too many attempts. Request a new code.")
    if not otp.codes_match(body.code, acc.reset_code_hash, request.app.state.jwt_secret):
        acc.reset_attempts += 1
        users.save(acc)
        raise invalid
    _check_password(body.new_password)
    acc.password_hash = hash_password(body.new_password)
    acc.reset_code_hash, acc.reset_expires_at, acc.reset_attempts = None, None, 0
    users.save(acc)
    return MessageOut(message="Password updated. You can log in now.")


# ---------------------------------------------------------------- logged in
@router.get("/me", response_model=UserOut)
def me(account: CurrentAccount):
    return account


@router.post("/change-password", response_model=MessageOut)
def change_password(body: ChangePasswordIn, account: CurrentAccount, users: Users):
    if not verify_password(body.current_password, account.password_hash):
        raise HTTPException(400, "Current password is wrong")
    _check_password(body.new_password)
    account.password_hash = hash_password(body.new_password)
    users.save(account)
    return MessageOut(message="Password changed")


# ---------------------------------------------------------------- managers only
@router.get("/users", response_model=list[UserOut])
def list_users(_: Manager, users: Users):
    return users.all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreateIn, _: Manager, users: Users):
    if users.get_by_email(body.email):
        raise HTTPException(400, "An account with this email already exists")
    _check_password(body.password)
    return users.add(body.name, body.email, body.role, hash_password(body.password))


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdateIn, me_: Manager, users: Users):
    acc = users.get(user_id)
    if acc is None:
        raise HTTPException(404, "User not found")
    if acc.id == me_.id and (body.role == "staff" or body.active is False):
        raise HTTPException(400, "You can't demote or disable your own account")
    for field_name, value in body.model_dump(exclude_none=True).items():
        setattr(acc, field_name, value)
    users.save(acc)
    return acc

