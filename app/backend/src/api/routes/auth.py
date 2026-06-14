"""Authentication routes: register, login (JWT), me, and Google OAuth."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from src.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from src.auth import oauth
from src.auth.deps import require_user
from src.auth.security import create_access_token, hash_password, verify_password
from src.core.config import settings
from src.db import repository as repo
from src.db.base import get_db
from src.db.models import User

router = APIRouter()


def _token_for(user: User) -> TokenResponse:
    token = create_access_token(user.id, email=user.email, name=user.full_name)
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "email": user.email, "full_name": user.full_name},
    )


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if repo.get_user_by_email(db, body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")
    user = repo.create_user(
        db,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name or "",
    )
    return _token_for(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = repo.get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    return _token_for(user)


@router.get("/me")
def me(user: User = Depends(require_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "oauth_provider": user.oauth_provider}


# ---- Google OAuth -------------------------------------------------------- #
@router.get("/google/login")
def google_login():
    if not settings.google_oauth_enabled:
        raise HTTPException(status_code=400, detail="Google OAuth not configured.")
    return {"authorize_url": oauth.build_authorize_url()}


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    if not settings.google_oauth_enabled:
        raise HTTPException(status_code=400, detail="Google OAuth not configured.")
    info = oauth.exchange_code_for_userinfo(code)
    email = (info.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Google did not return an email.")
    user = repo.get_user_by_email(db, email)
    if user is None:
        user = repo.create_user(
            db, email=email, full_name=info.get("name", ""), oauth_provider="google"
        )
    token = create_access_token(user.id, email=user.email, name=user.full_name)
    # Hand the token back to the SPA via a redirect fragment.
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/?token={token}")
