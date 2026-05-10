from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    portfolio_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(20), ForeignKey("profiles.profile_id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="enabled")  # enabled | paused | archived
    in_budget: Mapped[bool] = mapped_column(default=True)

    budget_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_currency_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    budget_policy: Mapped[str | None] = mapped_column(String(32), nullable=True)  # dateRange | monthlyRecurring
    budget_start_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    budget_end_date: Mapped[str | None] = mapped_column(String(16), nullable=True)

    served_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    creation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
