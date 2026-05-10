from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_lwa_headers
from app.models.profile import Profile

router = APIRouter(tags=["profiles"])


def _to_dict(p: Profile) -> dict:
    return {
        "profileId": int(p.profile_id),
        "countryCode": p.country_code,
        "currencyCode": p.currency_code,
        "timezone": p.timezone,
        "dailyBudget": p.daily_budget,
        "accountInfo": {
            "marketplaceStringId": p.marketplace_string_id,
            "id": p.account_id,
            "type": p.account_type,
            "name": p.account_name,
            "subType": p.sub_type or None,
            "validPaymentMethod": p.valid_payment_method,
        },
    }


@router.get("/v2/profiles")
def list_profiles(
    _: Annotated[AuthContext, Depends(require_lwa_headers)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return [_to_dict(p) for p in db.query(Profile).all()]


@router.get("/v2/profiles/{profile_id}")
def get_profile(
    profile_id: str,
    _: Annotated[AuthContext, Depends(require_lwa_headers)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    p = db.query(Profile).filter(Profile.profile_id == profile_id).first()
    if p is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "404", "details": f"Profile {profile_id} not found"},
        )
    return _to_dict(p)
