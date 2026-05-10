from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sd import SDTarget
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sd import SDTargetCreate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sd/targets", tags=["sd-targets"])


def _to_dict(t: SDTarget) -> dict[str, Any]:
    return {
        "targetId": t.target_id,
        "campaignId": t.campaign_id,
        "adGroupId": t.ad_group_id,
        "expression": t.expression,
        "expressionType": t.expression_type,
        "state": t.state,
        "bid": t.bid,
    }


@router.post("/list")
def list_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SDTarget).filter(SDTarget.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"targets": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: list[SDTargetCreate] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        tid = numeric_id(11)
        t = SDTarget(
            target_id=tid,
            campaign_id=item.campaignId,
            ad_group_id=item.adGroupId,
            profile_id=auth.profile_id,
            expression=[e.model_dump() for e in item.expression],
            expression_type=item.expressionType.upper(),
            state=item.state.upper(),
            bid=item.bid,
        )
        db.add(t)
        out.append({"index": i, "targetId": tid, "code": "SUCCESS"})
    db.commit()
    return out


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_targets(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: list[dict[str, Any]] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        tid = item.get("targetId")
        if not tid:
            out.append({"index": i, "code": "INVALID_ARGUMENT", "details": "targetId required"})
            continue
        t = (
            db.query(SDTarget)
            .filter(SDTarget.profile_id == auth.profile_id, SDTarget.target_id == tid)
            .first()
        )
        if t is None:
            out.append({"index": i, "targetId": tid, "code": "NOT_FOUND"})
            continue
        if "state" in item:
            t.state = str(item["state"]).upper()
        if "bid" in item:
            t.bid = float(item["bid"])
        t.last_updated_at = datetime.utcnow()
        out.append({"index": i, "targetId": t.target_id, "code": "SUCCESS"})
    db.commit()
    return out


@router.delete("/{target_id}")
def delete_target(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    target_id: str = Path(...),
) -> dict[str, Any]:
    t = (
        db.query(SDTarget)
        .filter(SDTarget.profile_id == auth.profile_id, SDTarget.target_id == target_id)
        .first()
    )
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(t)
    db.commit()
    return {"targetId": target_id, "code": "SUCCESS"}
