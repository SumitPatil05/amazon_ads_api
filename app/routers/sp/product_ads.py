from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sp import SPProductAd
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sp_v3 import ProductAdCreate, ProductAdUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sp/productAds", tags=["sp-product-ads"])


def _ts(dt: datetime | None) -> str | None:
    return (dt.isoformat() + "Z") if dt else None


def _to_dict(a: SPProductAd) -> dict[str, Any]:
    return {
        "adId": a.ad_id,
        "campaignId": a.campaign_id,
        "adGroupId": a.ad_group_id,
        "asin": a.asin,
        "sku": a.sku,
        "state": a.state,
        "extendedData": {
            "creationDateTime": _ts(a.created_at),
            "lastUpdateDateTime": _ts(a.last_updated_at),
            "servingStatus": "AD_STATUS_LIVE" if a.state == "ENABLED" else "AD_PAUSED",
        },
    }


@router.post("/list")
def list_product_ads(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SPProductAd).filter(SPProductAd.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    rows = apply_id_filter(rows, (body.get("adIdFilter") or {}).get("include"), attr="ad_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"productAds": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_product_ads(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("productAds") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = ProductAdCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        if not data.asin and not data.sku:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": "asin or sku required"})
            continue
        aid = numeric_id(11)
        now = datetime.utcnow()
        a = SPProductAd(
            ad_id=aid,
            campaign_id=data.campaignId,
            ad_group_id=data.adGroupId,
            profile_id=auth.profile_id,
            asin=data.asin,
            sku=data.sku,
            state=data.state.upper(),
            created_at=now,
            last_updated_at=now,
        )
        db.add(a)
        success.append({"index": i, "adId": aid, "productAd": _to_dict(a)})
    db.commit()
    return {"productAds": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_product_ads(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("productAds") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = ProductAdUpdate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        a = (
            db.query(SPProductAd)
            .filter(SPProductAd.profile_id == auth.profile_id, SPProductAd.ad_id == data.adId)
            .first()
        )
        if a is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Product ad {data.adId} not found"})
            continue
        if data.state is not None:
            a.state = data.state.upper()
        a.last_updated_at = datetime.utcnow()
        success.append({"index": i, "adId": a.ad_id, "productAd": _to_dict(a)})
    db.commit()
    return {"productAds": {"success": success, "error": error}}


@router.delete("/{ad_id}")
def delete_product_ad(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    ad_id: str = Path(...),
) -> dict[str, Any]:
    a = (
        db.query(SPProductAd)
        .filter(SPProductAd.profile_id == auth.profile_id, SPProductAd.ad_id == ad_id)
        .first()
    )
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(a)
    db.commit()
    return {"adId": ad_id, "code": "SUCCESS"}
