from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sb import SBTarget
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sb_v4 import SBTargetCreate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sb/v4/targets", tags=["sb-targets"])


def _to_dict(t: SBTarget) -> dict[str, Any]:
    return {
        "targetId": t.target_id,
        "campaignId": t.campaign_id,
        "adGroupId": t.ad_group_id,
        "expression": t.expression,
        "expressionType": t.expression_type,
        "bid": t.bid,
        "state": t.state,
    }


@router.post("/list")
def list_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SBTarget).filter(SBTarget.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"targets": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("targets") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = SBTargetCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        tid = numeric_id(11)
        t = SBTarget(
            target_id=tid,
            campaign_id=data.campaignId,
            ad_group_id=data.adGroupId,
            profile_id=auth.profile_id,
            expression=[e.model_dump() for e in data.expression],
            expression_type=data.expressionType.upper(),
            bid=data.bid,
            state=data.state.upper(),
        )
        db.add(t)
        success.append({"index": i, "targetId": tid, "target": _to_dict(t)})
    db.commit()
    return {"targets": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("targets") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        tid = item.get("targetId")
        if not tid:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": "targetId required"})
            continue
        t = (
            db.query(SBTarget)
            .filter(SBTarget.profile_id == auth.profile_id, SBTarget.target_id == tid)
            .first()
        )
        if t is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Target {tid} not found"})
            continue
        if "state" in item:
            t.state = str(item["state"]).upper()
        if "bid" in item:
            t.bid = float(item["bid"])
        t.last_updated_at = datetime.utcnow()
        success.append({"index": i, "targetId": t.target_id, "target": _to_dict(t)})
    db.commit()
    return {"targets": {"success": success, "error": error}}


@router.delete("/{target_id}")
def delete_target(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    target_id: str = Path(...),
) -> dict[str, Any]:
    t = (
        db.query(SBTarget)
        .filter(SBTarget.profile_id == auth.profile_id, SBTarget.target_id == target_id)
        .first()
    )
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(t)
    db.commit()
    return {"targetId": target_id, "code": "SUCCESS"}
