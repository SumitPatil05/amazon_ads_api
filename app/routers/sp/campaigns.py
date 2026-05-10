from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sp import SPCampaign
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sp_v3 import CampaignCreate, CampaignUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sp/campaigns", tags=["sp-campaigns"])


def _ts(dt: datetime | None) -> str | None:
    return (dt.isoformat() + "Z") if dt else None


def _to_dict(c: SPCampaign) -> dict[str, Any]:
    return {
        "campaignId": c.campaign_id,
        "portfolioId": c.portfolio_id,
        "name": c.name,
        "state": c.state,
        "targetingType": c.targeting_type,
        "dailyBudget": c.daily_budget,
        "budget": {"budget": c.daily_budget, "budgetType": "DAILY"},
        "dynamicBidding": c.dynamic_bidding or {"strategy": "LEGACY_FOR_SALES"},
        "startDate": c.start_date,
        "endDate": c.end_date,
        "tags": c.tags or {},
        "extendedData": {
            "creationDateTime": _ts(c.created_at),
            "lastUpdateDateTime": _ts(c.last_updated_at),
            "servingStatus": "CAMPAIGN_STATUS_ENABLED" if c.state == "ENABLED" else "CAMPAIGN_PAUSED",
        },
    }


@router.post("/list")
def list_campaigns(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SPCampaign).filter(SPCampaign.profile_id == auth.profile_id).all()

    state_filter = (body.get("stateFilter") or {}).get("include")
    rows = apply_state_filter(rows, state_filter)

    cid_filter = (body.get("campaignIdFilter") or {}).get("include")
    rows = apply_id_filter(rows, cid_filter, attr="campaign_id")

    pid_filter = (body.get("portfolioIdFilter") or {}).get("include")
    rows = apply_id_filter(rows, pid_filter, attr="portfolio_id")

    name_filter = (body.get("nameFilter") or {}).get("include")
    if name_filter:
        names = {str(n) for n in name_filter}
        rows = [r for r in rows if r.name in names]

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
            data = CampaignCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        cid = numeric_id(11)
        budget = data.dailyBudget if data.dailyBudget is not None else (data.budget.budget if data.budget else 10.0)
        now = datetime.utcnow()
        c = SPCampaign(
            campaign_id=cid,
            profile_id=auth.profile_id,
            portfolio_id=data.portfolioId,
            name=data.name,
            state=data.state.upper(),
            targeting_type=data.targetingType.upper(),
            daily_budget=budget,
            start_date=data.startDate,
            end_date=data.endDate,
            dynamic_bidding=data.dynamicBidding.model_dump() if data.dynamicBidding else {"strategy": "LEGACY_FOR_SALES"},
            tags=data.tags or {},
            created_at=now,
            last_updated_at=now,
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
            data = CampaignUpdate.model_validate(item)
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
        if data.name is not None:
            c.name = data.name
        if data.state is not None:
            c.state = data.state.upper()
        if data.portfolioId is not None:
            c.portfolio_id = data.portfolioId
        if data.dailyBudget is not None:
            c.daily_budget = data.dailyBudget
        elif data.budget is not None:
            c.daily_budget = data.budget.budget
        if data.startDate is not None:
            c.start_date = data.startDate
        if data.endDate is not None:
            c.end_date = data.endDate
        if data.dynamicBidding is not None:
            c.dynamic_bidding = data.dynamicBidding.model_dump()
        if data.tags is not None:
            c.tags = data.tags
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
        db.query(SPCampaign)
        .filter(SPCampaign.profile_id == auth.profile_id, SPCampaign.campaign_id == campaign_id)
        .first()
    )
    if c is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "404", "details": f"Campaign {campaign_id} not found"},
        )
    db.delete(c)
    db.commit()
    return {"campaignId": campaign_id, "code": "SUCCESS"}
