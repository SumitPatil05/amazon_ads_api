from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sd import SDProductAd
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sd import SDProductAdCreate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sd/productAds", tags=["sd-product-ads"])


def _to_dict(a: SDProductAd) -> dict[str, Any]:
    return {
        "adId": a.ad_id,
        "campaignId": a.campaign_id,
        "adGroupId": a.ad_group_id,
        "asin": a.asin,
        "sku": a.sku,
        "state": a.state,
    }


@router.post("/list")
def list_product_ads(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SDProductAd).filter(SDProductAd.profile_id == auth.profile_id).all()
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
    body: list[SDProductAdCreate] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        if not item.asin and not item.sku:
            out.append({"index": i, "code": "INVALID_ARGUMENT", "details": "asin or sku required"})
            continue
        aid = numeric_id(11)
        a = SDProductAd(
            ad_id=aid,
            campaign_id=item.campaignId,
            ad_group_id=item.adGroupId,
            profile_id=auth.profile_id,
            asin=item.asin,
            sku=item.sku,
            state=item.state.upper(),
        )
        db.add(a)
        out.append({"index": i, "adId": aid, "code": "SUCCESS"})
    db.commit()
    return out


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_product_ads(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: list[dict[str, Any]] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        aid = item.get("adId")
        if not aid:
            out.append({"index": i, "code": "INVALID_ARGUMENT", "details": "adId required"})
            continue
        a = (
            db.query(SDProductAd)
            .filter(SDProductAd.profile_id == auth.profile_id, SDProductAd.ad_id == aid)
            .first()
        )
        if a is None:
            out.append({"index": i, "adId": aid, "code": "NOT_FOUND"})
            continue
        if "state" in item:
            a.state = str(item["state"]).upper()
        a.last_updated_at = datetime.utcnow()
        out.append({"index": i, "adId": a.ad_id, "code": "SUCCESS"})
    db.commit()
    return out


@router.delete("/{ad_id}")
def delete_product_ad(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    ad_id: str = Path(...),
) -> dict[str, Any]:
    a = (
        db.query(SDProductAd)
        .filter(SDProductAd.profile_id == auth.profile_id, SDProductAd.ad_id == ad_id)
        .first()
    )
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(a)
    db.commit()
    return {"adId": ad_id, "code": "SUCCESS"}
