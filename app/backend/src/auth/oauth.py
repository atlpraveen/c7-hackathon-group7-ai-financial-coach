"""Minimal Google OAuth2 (Authorization Code) flow.

Active only when GOOGLE_CLIENT_ID/SECRET are configured. Uses httpx for the
token exchange + userinfo lookup. Kept dependency-light and provider-specific
(Google) — the same pattern extends to other OAuth providers.
"""
from __future__ import annotations

from urllib.parse import urlencode

from src.core.config import settings

_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


def build_authorize_url(state: str = "") -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URL,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    if state:
        params["state"] = state
    return f"{_AUTH_ENDPOINT}?{urlencode(params)}"


def exchange_code_for_userinfo(code: str) -> dict:
    """Exchange an auth code for the user's Google profile (email, name)."""
    import httpx

    token_resp = httpx.post(
        _TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.OAUTH_REDIRECT_URL,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json().get("access_token")
    info_resp = httpx.get(
        _USERINFO_ENDPOINT,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    info_resp.raise_for_status()
    return info_resp.json()
