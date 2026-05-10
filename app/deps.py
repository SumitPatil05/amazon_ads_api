from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.tokens import verify_access_token
from app.db import get_db
from app.services.ids import request_id


@dataclass
class AuthContext:
    client_id: str
    access_token: str
    profile_id: str | None
    claims: dict


def _amazon_error(code: str, details: str, http: int) -> HTTPException:
    return HTTPException(
        status_code=http,
        detail={"code": code, "details": details, "requestId": request_id()},
    )


def require_lwa_headers(
    authorization: Annotated[str | None, Header()] = None,
    amazon_advertising_api_clientid: Annotated[
        str | None, Header(alias="Amazon-Advertising-API-ClientId")
    ] = None,
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _amazon_error(
            "401",
            "Authorization header missing or not a Bearer token",
            status.HTTP_401_UNAUTHORIZED,
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = verify_access_token(token)
    except ValueError as exc:
        raise _amazon_error("401", f"Invalid access token: {exc}", status.HTTP_401_UNAUTHORIZED) from exc

    if not amazon_advertising_api_clientid:
        raise _amazon_error(
            "401",
            "Amazon-Advertising-API-ClientId header is required",
            status.HTTP_401_UNAUTHORIZED,
        )

    return AuthContext(
        client_id=amazon_advertising_api_clientid,
        access_token=token,
        profile_id=None,
        claims=claims,
    )


def require_profile_scope(
    auth: Annotated[AuthContext, Depends(require_lwa_headers)],
    amazon_advertising_api_scope: Annotated[
        str | None, Header(alias="Amazon-Advertising-API-Scope")
    ] = None,
    db: Annotated[Session, Depends(get_db)] = None,  # type: ignore[assignment]
) -> AuthContext:
    if not amazon_advertising_api_scope:
        raise _amazon_error(
            "401",
            "Amazon-Advertising-API-Scope (profile id) header is required",
            status.HTTP_401_UNAUTHORIZED,
        )

    from app.models.profile import Profile

    profile = db.query(Profile).filter(Profile.profile_id == amazon_advertising_api_scope).first()
    if profile is None:
        raise _amazon_error(
            "403",
            f"Profile {amazon_advertising_api_scope} not found or not authorized for this client",
            status.HTTP_403_FORBIDDEN,
        )

    return AuthContext(
        client_id=auth.client_id,
        access_token=auth.access_token,
        profile_id=profile.profile_id,
        claims=auth.claims,
    )
