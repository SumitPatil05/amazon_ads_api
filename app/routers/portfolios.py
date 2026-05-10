from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.portfolio import Portfolio
from app.schemas.portfolios import PortfolioCreate, PortfolioUpdate
from app.services.ids import numeric_id

router = APIRouter(tags=["portfolios"])


def _to_dict(p: Portfolio, *, extended: bool = False) -> dict:
    out = {
        "portfolioId": int(p.portfolio_id),
        "name": p.name,
        "state": p.state,
        "inBudget": p.in_budget,
        "budget": (
            {
                "amount": p.budget_amount,
                "currencyCode": p.budget_currency_code,
                "policy": p.budget_policy,
                "startDate": p.budget_start_date,
                "endDate": p.budget_end_date,
            }
            if p.budget_amount is not None
            else None
        ),
    }
    if extended:
        out.update(
            {
                "creationDate": int(p.creation_date.timestamp() * 1000),
                "lastUpdatedDate": int(p.last_updated_date.timestamp() * 1000),
                "servingStatus": "PORTFOLIO_STATUS_ENABLED" if p.state == "enabled" else "PORTFOLIO_PAUSED",
            }
        )
    return out


@router.get("/portfolios")
def list_portfolios(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    portfolioIdFilter: str | None = Query(default=None),
    portfolioNameFilter: str | None = Query(default=None),
    portfolioStateFilter: str | None = Query(default=None),
) -> list[dict]:
    q = db.query(Portfolio).filter(Portfolio.profile_id == auth.profile_id)
    if portfolioIdFilter:
        ids = [s.strip() for s in portfolioIdFilter.split(",") if s.strip()]
        q = q.filter(Portfolio.portfolio_id.in_(ids))
    if portfolioNameFilter:
        q = q.filter(Portfolio.name.in_([s.strip() for s in portfolioNameFilter.split(",")]))
    if portfolioStateFilter:
        q = q.filter(Portfolio.state.in_([s.strip() for s in portfolioStateFilter.split(",")]))
    return [_to_dict(p) for p in q.all()]


@router.get("/portfolios/extended")
def list_portfolios_extended(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return [_to_dict(p, extended=True) for p in db.query(Portfolio).filter(Portfolio.profile_id == auth.profile_id).all()]


@router.get("/portfolios/{portfolio_id}")
def get_portfolio(
    portfolio_id: str,
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    p = (
        db.query(Portfolio)
        .filter(Portfolio.profile_id == auth.profile_id, Portfolio.portfolio_id == portfolio_id)
        .first()
    )
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "404", "details": f"Portfolio {portfolio_id} not found"},
        )
    return _to_dict(p)


@router.post("/portfolios", status_code=status.HTTP_207_MULTI_STATUS)
def create_portfolios(
    body: list[PortfolioCreate],
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    out: list[dict] = []
    for i, item in enumerate(body):
        pid = numeric_id(11)
        p = Portfolio(
            portfolio_id=pid,
            profile_id=auth.profile_id,
            name=item.name,
            state=item.state,
            in_budget=True,
            budget_amount=item.budget.amount if item.budget else None,
            budget_currency_code=item.budget.currencyCode if item.budget else None,
            budget_policy=item.budget.policy if item.budget else None,
            budget_start_date=item.budget.startDate if item.budget else None,
            budget_end_date=item.budget.endDate if item.budget else None,
        )
        db.add(p)
        out.append({"index": i, "portfolioId": int(pid), "code": "SUCCESS"})
    db.commit()
    return out


@router.put("/portfolios", status_code=status.HTTP_207_MULTI_STATUS)
def update_portfolios(
    body: list[PortfolioUpdate],
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    out: list[dict] = []
    for i, item in enumerate(body):
        p = (
            db.query(Portfolio)
            .filter(Portfolio.profile_id == auth.profile_id, Portfolio.portfolio_id == str(item.portfolioId))
            .first()
        )
        if p is None:
            out.append({"index": i, "portfolioId": item.portfolioId, "code": "NOT_FOUND"})
            continue
        if item.name is not None:
            p.name = item.name
        if item.state is not None:
            p.state = item.state
        if item.budget is not None:
            p.budget_amount = item.budget.amount
            p.budget_currency_code = item.budget.currencyCode
            p.budget_policy = item.budget.policy
            p.budget_start_date = item.budget.startDate
            p.budget_end_date = item.budget.endDate
        p.last_updated_date = datetime.utcnow()
        out.append({"index": i, "portfolioId": item.portfolioId, "code": "SUCCESS"})
    db.commit()
    return out
