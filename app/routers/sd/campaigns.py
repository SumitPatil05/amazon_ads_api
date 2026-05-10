from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sd import SDCampaign
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sd import SDCampaignCreate, SDCampaignUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sd/campaigns", tags=["sd-campaigns"])


def _to_dict(c: SDCampaign) -> dict[str, Any]:
    return {
        "campaignId": c.campaign_id,
        "name": c.name,
        "tactic": c.tactic,
        "state": c.state,
        "portfolioId": c.portfolio_id,
        "budgetType": c.budget_type,
        "budget": c.budget,
        "startDate": c.start_date,
        "endDate": c.end_date,
        "costType": c.cost_type,
    }


@router.post("/list")
def list_campaigns(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SDCampaign).filter(SDCampaign.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"campaigns": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_campaigns(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: list[SDCampaignCreate] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        cid = numeric_id(11)
        c = SDCampaign(
            campaign_id=cid,
            profile_id=auth.profile_id,
            portfolio_id=item.portfolioId,
            name=item.name,
            state=item.state.upper(),
            tactic=item.tactic.upper(),
            budget_type=item.budgetType.lower(),
            budget=item.budget,
            start_date=item.startDate,
            end_date=item.endDate,
            cost_type=item.costType.lower(),
        )
        db.add(c)
        out.append({"index": i, "campaignId": cid, "code": "SUCCESS"})
    db.commit()
    return out


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_campaigns(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: list[SDCampaignUpdate] = Body(...),
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, item in enumerate(body):
        c = (
            db.query(SDCampaign)
            .filter(SDCampaign.profile_id == auth.profile_id, SDCampaign.campaign_id == item.campaignId)
            .first()
        )
        if c is None:
            out.append({"index": i, "campaignId": item.campaignId, "code": "NOT_FOUND"})
            continue
        if item.name is not None:
            c.name = item.name
        if item.state is not None:
            c.state = item.state.upper()
        if item.budget is not None:
            c.budget = item.budget
        c.last_updated_at = datetime.utcnow()
        out.append({"index": i, "campaignId": c.campaign_id, "code": "SUCCESS"})
    db.commit()
    return out


@router.delete("/{campaign_id}")
def delete_campaign(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    campaign_id: str = Path(...),
) -> dict[str, Any]:
    c = (
        db.query(SDCampaign)
        .filter(SDCampaign.profile_id == auth.profile_id, SDCampaign.campaign_id == campaign_id)
        .first()
    )
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(c)
    db.commit()
    return {"campaignId": campaign_id, "code": "SUCCESS"}
