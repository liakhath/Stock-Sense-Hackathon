"""User accounts. In-memory repo for tests / no-DB mode, SQL repo for Supabase."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.engine import Engine

ROLES = ("manager", "staff")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt):
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class Account:
    id: int
    name: str
    email: str
    role: str                                   # manager | staff
    password_hash: str = ""
    active: bool = True
    created_at: datetime = field(default_factory=_now)
    reset_code_hash: Optional[str] = None
    reset_expires_at: Optional[datetime] = None
    reset_attempts: int = 0

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"


class UserRepo:
    """In-memory users (tests, or running without DATABASE_URL)."""

    def __init__(self) -> None:
        self._users: dict[int, Account] = {}
        self._lock = threading.RLock()

    def count(self) -> int:
        return len(self._users)

    def get(self, user_id: int) -> Optional[Account]:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[Account]:
        email = email.strip().lower()
        return next((u for u in self._users.values() if u.email == email), None)

    def all(self) -> list[Account]:
        return sorted(self._users.values(), key=lambda u: u.id)

    def add(self, name: str, email: str, role: str, password_hash: str) -> Account:
        with self._lock:
            acc = Account(id=max(self._users, default=0) + 1, name=name.strip(),
                          email=email.strip().lower(), role=role, password_hash=password_hash)
            self._users[acc.id] = acc
            self._write(acc)
            return acc

    def save(self, acc: Account) -> None:
        with self._lock:
            self._users[acc.id] = acc
            self._write(acc)

    def _write(self, acc: Account) -> None:
        """Persist one account. No-op in memory."""


class SqlUserRepo(UserRepo):
    """Loads users into memory at startup, writes every change straight to the database."""

    def __init__(self, db: Engine) -> None:
        super().__init__()
        from app.db import tables as t
        self.db, self.table = db, t.users
        t.metadata.create_all(db, tables=[t.users])
        with db.connect() as c:
            for r in c.execute(select(t.users)).mappings():
                self._users[r["id"]] = Account(
                    id=r["id"], name=r["name"], email=r["email"], role=r["role"],
                    password_hash=r["password_hash"], active=r["active"],
                    created_at=_aware(r["created_at"]), reset_code_hash=r["reset_code_hash"],
                    reset_expires_at=_aware(r["reset_expires_at"]),
                    reset_attempts=r["reset_attempts"],
                )

    def _write(self, acc: Account) -> None:
        row = {"id": acc.id, "name": acc.name, "email": acc.email, "role": acc.role,
               "password_hash": acc.password_hash, "active": acc.active,
               "created_at": acc.created_at, "reset_code_hash": acc.reset_code_hash,
               "reset_expires_at": acc.reset_expires_at, "reset_attempts": acc.reset_attempts}
        with self.db.begin() as c:
            if c.dialect.name == "postgresql":
                from sqlalchemy.dialects.postgresql import insert
            else:
                from sqlalchemy.dialects.sqlite import insert
            stmt = insert(self.table)
            c.execute(stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={k: stmt.excluded[k] for k in row if k != "id"}), row)
