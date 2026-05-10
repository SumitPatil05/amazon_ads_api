from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sp import SPAdGroup, SPCampaign
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sp_v3 import AdGroupCreate, AdGroupUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sp/adGroups", tags=["sp-ad-groups"])


def _ts(dt: datetime | None) -> str | None:
    return (dt.isoformat() + "Z") if dt else None


def _to_dict(a: SPAdGroup) -> dict[str, Any]:
    return {
        "adGroupId": a.ad_group_id,
        "campaignId": a.campaign_id,
        "name": a.name,
        "state": a.state,
        "defaultBid": a.default_bid,
        "extendedData": {
            "creationDateTime": _ts(a.created_at),
            "lastUpdateDateTime": _ts(a.last_updated_at),
            "servingStatus": "AD_GROUP_STATUS_ENABLED" if a.state == "ENABLED" else "AD_GROUP_PAUSED",
        },
    }


@router.post("/list")
def list_ad_groups(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SPAdGroup).filter(SPAdGroup.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"adGroups": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_ad_groups(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("adGroups") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = AdGroupCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        c = (
            db.query(SPCampaign)
            .filter(SPCampaign.profile_id == auth.profile_id, SPCampaign.campaign_id == data.campaignId)
            .first()
        )
        if c is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Campaign {data.campaignId} not found"})
            continue
        agid = numeric_id(11)
        now = datetime.utcnow()
        a = SPAdGroup(
            ad_group_id=agid,
            campaign_id=data.campaignId,
            profile_id=auth.profile_id,
            name=data.name,
            state=data.state.upper(),
            default_bid=data.defaultBid,
            created_at=now,
            last_updated_at=now,
        )
        db.add(a)
        success.append({"index": i, "adGroupId": agid, "adGroup": _to_dict(a)})
    db.commit()
    return {"adGroups": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_ad_groups(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("adGroups") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = AdGroupUpdate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        a = (
            db.query(SPAdGroup)
            .filter(SPAdGroup.profile_id == auth.profile_id, SPAdGroup.ad_group_id == data.adGroupId)
            .first()
        )
        if a is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Ad group {data.adGroupId} not found"})
            continue
        if data.name is not None:
            a.name = data.name
        if data.state is not None:
            a.state = data.state.upper()
        if data.defaultBid is not None:
            a.default_bid = data.defaultBid
        a.last_updated_at = datetime.utcnow()
        success.append({"index": i, "adGroupId": a.ad_group_id, "adGroup": _to_dict(a)})
    db.commit()
    return {"adGroups": {"success": success, "error": error}}


@router.delete("/{ad_group_id}")
def delete_ad_group(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    ad_group_id: str = Path(...),
) -> dict[str, Any]:
    a = (
        db.query(SPAdGroup)
        .filter(SPAdGroup.profile_id == auth.profile_id, SPAdGroup.ad_group_id == ad_group_id)
        .first()
    )
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(a)
    db.commit()
    return {"adGroupId": ad_group_id, "code": "SUCCESS"}
