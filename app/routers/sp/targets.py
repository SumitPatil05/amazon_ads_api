from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sp import SPTarget
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sp_v3 import TargetCreate, TargetUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sp/targets", tags=["sp-targets"])


def _ts(dt: datetime | None) -> str | None:
    return (dt.isoformat() + "Z") if dt else None


def _to_dict(t: SPTarget) -> dict[str, Any]:
    return {
        "targetId": t.target_id,
        "campaignId": t.campaign_id,
        "adGroupId": t.ad_group_id,
        "expression": t.expression,
        "expressionType": t.expression_type,
        "state": t.state,
        "bid": t.bid,
        "extendedData": {
            "creationDateTime": _ts(t.created_at),
            "lastUpdateDateTime": _ts(t.last_updated_at),
            "servingStatus": "TARGETING_CLAUSE_STATUS_LIVE" if t.state == "ENABLED" else "TARGETING_CLAUSE_PAUSED",
        },
    }


@router.post("/list")
def list_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SPTarget).filter(SPTarget.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    rows = apply_id_filter(rows, (body.get("targetIdFilter") or {}).get("include"), attr="target_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"targetingClauses": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("targetingClauses") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = TargetCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        tid = numeric_id(11)
        now = datetime.utcnow()
        t = SPTarget(
            target_id=tid,
            campaign_id=data.campaignId,
            ad_group_id=data.adGroupId,
            profile_id=auth.profile_id,
            expression=[e.model_dump() for e in data.expression],
            expression_type=data.expressionType.upper(),
            state=data.state.upper(),
            bid=data.bid,
            created_at=now,
            last_updated_at=now,
        )
        db.add(t)
        success.append({"index": i, "targetId": tid, "targetingClause": _to_dict(t)})
    db.commit()
    return {"targetingClauses": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("targetingClauses") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = TargetUpdate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        t = (
            db.query(SPTarget)
            .filter(SPTarget.profile_id == auth.profile_id, SPTarget.target_id == data.targetId)
            .first()
        )
        if t is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Target {data.targetId} not found"})
            continue
        if data.state is not None:
            t.state = data.state.upper()
        if data.bid is not None:
            t.bid = data.bid
        if data.expression is not None:
            t.expression = [e.model_dump() for e in data.expression]
        t.last_updated_at = datetime.utcnow()
        success.append({"index": i, "targetId": t.target_id, "targetingClause": _to_dict(t)})
    db.commit()
    return {"targetingClauses": {"success": success, "error": error}}


@router.delete("/{target_id}")
def delete_target(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    target_id: str = Path(...),
) -> dict[str, Any]:
    t = (
        db.query(SPTarget)
        .filter(SPTarget.profile_id == auth.profile_id, SPTarget.target_id == target_id)
        .first()
    )
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(t)
    db.commit()
    return {"targetId": target_id, "code": "SUCCESS"}
