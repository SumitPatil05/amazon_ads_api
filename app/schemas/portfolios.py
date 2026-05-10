from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Budget(BaseModel):
    amount: float | None = None
    currencyCode: str | None = None
    policy: str | None = None  # dateRange | monthlyRecurring
    startDate: str | None = None
    endDate: str | None = None


class Portfolio(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    portfolioId: int
    name: str
    state: str = "enabled"
    inBudget: bool = True
    budget: Budget | None = None


class PortfolioCreate(BaseModel):
    name: str
    state: str = "enabled"
    budget: Budget | None = None


class PortfolioUpdate(BaseModel):
    portfolioId: int
    name: str | None = None
    state: str | None = None
    budget: Budget | None = None
