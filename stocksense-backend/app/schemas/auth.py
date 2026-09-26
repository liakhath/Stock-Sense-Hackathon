import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from .common import OutModel

Role = Literal["manager", "staff"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class _WithEmail(BaseModel):
    email: str = Field(examples=["manager@stocksense.demo"])

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v


class SignupIn(_WithEmail):
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(examples=["demo1234"])


class LoginIn(_WithEmail):
    password: str


class ForgotPasswordIn(_WithEmail):
    pass


class ResetPasswordIn(_WithEmail):
    code: str = Field(min_length=6, max_length=6, examples=["123456"])
    new_password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


class UserCreateIn(SignupIn):
    role: Role = "staff"


class UserUpdateIn(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    role: Optional[Role] = None
    active: Optional[bool] = None


class UserOut(OutModel):
    id: int
    name: str
    email: str
    role: Role
    active: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int              # seconds
    user: UserOut


class ForgotPasswordOut(BaseModel):
    message: str
    demo_code: Optional[str] = None   # only in OTP demo mode, only for registered emails


class MessageOut(BaseModel):
    message: str
