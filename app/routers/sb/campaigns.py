from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sb import SBCampaign
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sb_v4 import SBCampaignCreate, SBCampaignUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sb/v4/campaigns", tags=["sb-campaigns"])


def _to_dict(c: SBCampaign) -> dict[str, Any]:
    return {
        "campaignId": c.campaign_id,
        "name": c.name,
        "state": c.state,
        "portfolioId": c.portfolio_id,
        "budgetType": c.budget_type,
        "budget": c.budget,
        "startDate": c.start_date,
        "endDate": c.end_date,
        "bidding": c.bidding or {"bidOptimizeForConversions": True},
        "brandEntityId": c.brand_entity_id,
    }


@router.post("/list")
def list_campaigns(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SBCampaign).filter(SBCampaign.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"campaigns": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_campaigns(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("campaigns") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = SBCampaignCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        cid = numeric_id(11)
        c = SBCampaign(
            campaign_id=cid,
            profile_id=auth.profile_id,
            portfolio_id=data.portfolioId,
            name=data.name,
            state=data.state.upper(),
            budget_type=data.budgetType.upper(),
            budget=data.budget,
            start_date=data.startDate,
            end_date=data.endDate,
            bidding=data.bidding.model_dump() if data.bidding else {"bidOptimizeForConversions": True},
            brand_entity_id=data.brandEntityId,
        )
        db.add(c)
        success.append({"index": i, "campaignId": cid, "campaign": _to_dict(c)})
    db.commit()
    return {"campaigns": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_campaigns(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("campaigns") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = SBCampaignUpdate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        c = (
            db.query(SBCampaign)
            .filter(SBCampaign.profile_id == auth.profile_id, SBCampaign.campaign_id == data.campaignId)
            .first()
        )
        if c is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Campaign {data.campaignId} not found"})
            continue
        if data.name is not None:
            c.name = data.name
        if data.state is not None:
            c.state = data.state.upper()
        if data.budget is not None:
            c.budget = data.budget
        if data.bidding is not None:
            c.bidding = data.bidding.model_dump()
        c.last_updated_at = datetime.utcnow()
        success.append({"index": i, "campaignId": c.campaign_id, "campaign": _to_dict(c)})
    db.commit()
    return {"campaigns": {"success": success, "error": error}}


@router.delete("/{campaign_id}")
def delete_campaign(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    campaign_id: str = Path(...),
) -> dict[str, Any]:
    c = (
        db.query(SBCampaign)
        .filter(SBCampaign.profile_id == auth.profile_id, SBCampaign.campaign_id == campaign_id)
        .first()
    )
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(c)
    db.commit()
    return {"campaignId": campaign_id, "code": "SUCCESS"}
