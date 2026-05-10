from __future__ import annotations

import time
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings


def mint_access_token(client_id: str, refresh_token: str | None = None, ttl_sec: int | None = None) -> tuple[str, int]:
    settings = get_settings()
    ttl = ttl_sec or settings.ACCESS_TOKEN_TTL_SEC
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": "mock-lwa",
        "aud": "advertising-api",
        "iat": now,
        "exp": now + ttl,
        "client_id": client_id,
    }
    if refresh_token:
        claims["refresh_token_hint"] = refresh_token[:8]
    token = jwt.encode(claims, settings.LWA_JWT_SECRET, algorithm=settings.LWA_JWT_ALG)
    return token, ttl


def mint_refresh_token(client_id: str) -> str:
    # Amazon refresh tokens start with "Atzr|"
    return "Atzr|mock-" + jwt.encode(
        {"client_id": client_id, "iat": int(time.time()), "kind": "refresh"},
        get_settings().LWA_JWT_SECRET,
        algorithm=get_settings().LWA_JWT_ALG,
    )


def verify_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.LWA_JWT_SECRET,
            algorithms=[settings.LWA_JWT_ALG],
            audience="advertising-api",
        )
    except JWTError as exc:
        raise ValueError(str(exc)) from exc
