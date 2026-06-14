"""Auth dependencies.

``get_current_user`` resolves the bearer token to a User. To keep the app
instantly usable (no forced login), an *anonymous* request transparently falls
back to a shared ``guest@local`` account — so the demo works out of the box,
while registering/logging in gives a fully isolated per-user workspace.
``require_user`` is the strict variant for endpoints that must be authenticated.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.auth.security import decode_token
from src.db import repository as repo
from src.db.base import get_db
from src.db.models import User

GUEST_EMAIL = "guest@local"


def get_or_create_guest(db: Session) -> User:
    """Return the shared guest account, creating it idempotently.

    Concurrent anonymous requests can race to create it, so we treat a unique
    violation as "someone else just made it" and re-read.
    """
    guest = repo.get_user_by_email(db, GUEST_EMAIL)
    if guest is not None:
        return guest
    try:
        return repo.create_user(db, email=GUEST_EMAIL, full_name="Guest")
    except IntegrityError:
        db.rollback()
        guest = repo.get_user_by_email(db, GUEST_EMAIL)
        if guest is None:  # pragma: no cover - shouldn't happen
            raise
        return guest


def _bearer(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _bearer(authorization)
    if token:
        payload = decode_token(token)
        if payload:
            user = repo.get_user(db, int(payload.get("sub", 0)))
            if user:
                return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Anonymous → shared guest workspace.
    return get_or_create_guest(db)


def require_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = _bearer(authorization)
    payload = decode_token(token) if token else None
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = repo.get_user(db, int(payload.get("sub", 0)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user
