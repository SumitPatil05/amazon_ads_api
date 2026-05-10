from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sb import SBAdGroup, SBCreative
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sb_v4 import SBCreativeCreate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sb/v4/creatives", tags=["sb-creatives"])


def _to_dict(c: SBCreative) -> dict[str, Any]:
    return {
        "creativeId": c.creative_id,
        "adGroupId": c.ad_group_id,
        "campaignId": c.campaign_id,
        "creativeType": c.creative_type,
        "headline": c.headline,
        "brandName": c.brand_name,
        "brandLogoAssetId": c.brand_logo_asset_id,
        "videoAssetId": c.video_asset_id,
        "asins": c.asins or [],
        "state": c.state,
    }


@router.post("/list")
def list_creatives(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SBCreative).filter(SBCreative.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"creatives": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_creatives(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("creatives") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = SBCreativeCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        ag = (
            db.query(SBAdGroup)
            .filter(SBAdGroup.profile_id == auth.profile_id, SBAdGroup.ad_group_id == data.adGroupId)
            .first()
        )
        if ag is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Ad group {data.adGroupId} not found"})
            continue
        cid = "amzn1.assetlibrary.asset1." + numeric_id(8)
        c = SBCreative(
            creative_id=cid,
            ad_group_id=data.adGroupId,
            campaign_id=ag.campaign_id,
            profile_id=auth.profile_id,
            creative_type=data.creativeType,
            headline=data.headline,
            brand_name=data.brandName,
            brand_logo_asset_id=data.brandLogoAssetId,
            video_asset_id=data.videoAssetId,
            asins=data.asins,
            state=data.state.upper(),
        )
        db.add(c)
        success.append({"index": i, "creativeId": cid, "creative": _to_dict(c)})
    db.commit()
    return {"creatives": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_creatives(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("creatives") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        cid = item.get("creativeId")
        if not cid:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": "creativeId required"})
            continue
        c = (
            db.query(SBCreative)
            .filter(SBCreative.profile_id == auth.profile_id, SBCreative.creative_id == cid)
            .first()
        )
        if c is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Creative {cid} not found"})
            continue
        for key in ("headline", "brandName", "brandLogoAssetId", "videoAssetId"):
            if key in item:
                setattr(c, _camel_to_snake(key), item[key])
        if "asins" in item:
            c.asins = list(item["asins"])
        if "state" in item:
            c.state = str(item["state"]).upper()
        c.last_updated_at = datetime.utcnow()
        success.append({"index": i, "creativeId": c.creative_id, "creative": _to_dict(c)})
    db.commit()
    return {"creatives": {"success": success, "error": error}}


def _camel_to_snake(name: str) -> str:
    out = []
    for ch in name:
        if ch.isupper():
            out.append("_")
            out.append(ch.lower())
        else:
            out.append(ch)
    return "".join(out)


@router.delete("/{creative_id}")
def delete_creative(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    creative_id: str = Path(...),
) -> dict[str, Any]:
    c = (
        db.query(SBCreative)
        .filter(SBCreative.profile_id == auth.profile_id, SBCreative.creative_id == creative_id)
        .first()
    )
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(c)
    db.commit()
    return {"creativeId": creative_id, "code": "SUCCESS"}
