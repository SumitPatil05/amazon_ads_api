from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sd import SDAdGroup
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sd import SDAdGroupCreate, SDAdGroupUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sd/adGroups", tags=["sd-ad-groups"])


def _to_dict(a: SDAdGroup) -> dict[str, Any]:
    return {
        "adGroupId": a.ad_group_id,
        "campaignId": a.campaign_id,
        "name": a.name,
        "state": a.state,
        "defaultBid": a.default_bid,
        "bidOptimization": a.bid_optimization,
    }


@router.post("/list")
def list_ad_groups(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SDAdGroup).filter(SDAdGroup.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"adGroups": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_ad_groups(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: list[SDAdGroupCreate] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        agid = numeric_id(11)
        a = SDAdGroup(
            ad_group_id=agid,
            campaign_id=item.campaignId,
            profile_id=auth.profile_id,
            name=item.name,
            state=item.state.upper(),
            default_bid=item.defaultBid,
            bid_optimization=item.bidOptimization,
        )
        db.add(a)
        out.append({"index": i, "adGroupId": agid, "code": "SUCCESS"})
    db.commit()
    return out


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_ad_groups(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: list[SDAdGroupUpdate] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        a = (
            db.query(SDAdGroup)
            .filter(SDAdGroup.profile_id == auth.profile_id, SDAdGroup.ad_group_id == item.adGroupId)
            .first()
        )
        if a is None:
            out.append({"index": i, "adGroupId": item.adGroupId, "code": "NOT_FOUND"})
            continue
        if item.name is not None:
            a.name = item.name
        if item.state is not None:
            a.state = item.state.upper()
        if item.defaultBid is not None:
            a.default_bid = item.defaultBid
        a.last_updated_at = datetime.utcnow()
        out.append({"index": i, "adGroupId": a.ad_group_id, "code": "SUCCESS"})
    db.commit()
    return out


@router.delete("/{ad_group_id}")
def delete_ad_group(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    ad_group_id: str = Path(...),
) -> dict[str, Any]:
    a = (
        db.query(SDAdGroup)
        .filter(SDAdGroup.profile_id == auth.profile_id, SDAdGroup.ad_group_id == ad_group_id)
        .first()
    )
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(a)
    db.commit()
    return {"adGroupId": ad_group_id, "code": "SUCCESS"}
