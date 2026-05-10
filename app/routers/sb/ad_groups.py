from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sb import SBAdGroup
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sb_v4 import SBAdGroupCreate, SBAdGroupUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sb/v4/adGroups", tags=["sb-ad-groups"])


def _to_dict(a: SBAdGroup) -> dict[str, Any]:
    return {
        "adGroupId": a.ad_group_id,
        "campaignId": a.campaign_id,
        "name": a.name,
        "state": a.state,
    }


@router.post("/list")
def list_ad_groups(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SBAdGroup).filter(SBAdGroup.profile_id == auth.profile_id).all()
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
            data = SBAdGroupCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        agid = numeric_id(11)
        a = SBAdGroup(
            ad_group_id=agid,
            campaign_id=data.campaignId,
            profile_id=auth.profile_id,
            name=data.name,
            state=data.state.upper(),
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
            data = SBAdGroupUpdate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        a = (
            db.query(SBAdGroup)
            .filter(SBAdGroup.profile_id == auth.profile_id, SBAdGroup.ad_group_id == data.adGroupId)
            .first()
        )
        if a is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Ad group {data.adGroupId} not found"})
            continue
        if data.name is not None:
            a.name = data.name
        if data.state is not None:
            a.state = data.state.upper()
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
        db.query(SBAdGroup)
        .filter(SBAdGroup.profile_id == auth.profile_id, SBAdGroup.ad_group_id == ad_group_id)
        .first()
    )
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(a)
    db.commit()
    return {"adGroupId": ad_group_id, "code": "SUCCESS"}
