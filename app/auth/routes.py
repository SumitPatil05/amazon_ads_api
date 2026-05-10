from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, status

from app.auth.tokens import mint_access_token, mint_refresh_token
from app.config import get_settings

router = APIRouter(tags=["auth"])


# Path mirrors the real LWA endpoint: https://api.amazon.com/auth/o2/token
@router.post("/auth/o2/token")
def issue_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    refresh_token: str | None = Form(default=None),
    code: str | None = Form(default=None),
    redirect_uri: str | None = Form(default=None),
    scope: str | None = Form(default=None),
) -> dict:
    settings = get_settings()

    if grant_type not in {"refresh_token", "authorization_code", "client_credentials"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "unsupported_grant_type", "error_description": grant_type},
        )

    if grant_type == "refresh_token" and not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_request", "error_description": "refresh_token is required"},
        )
    if grant_type == "authorization_code" and not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_request", "error_description": "code is required"},
        )

    if settings.STRICT_AUTH:
        # Hook for stricter checks; the demo seed simply expects any non-empty values.
        if not (client_id and client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_client"},
            )

    access_token, ttl = mint_access_token(client_id, refresh_token)
    new_refresh = refresh_token or mint_refresh_token(client_id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": ttl,
        "scope": scope or "advertising::campaign_management",
    }
