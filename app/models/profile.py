from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Profile(Base):
    __tablename__ = "profiles"

    profile_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    daily_budget: Mapped[float] = mapped_column(Float, default=0.0)
    account_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_type: Mapped[str] = mapped_column(String(16), default="seller")  # seller | vendor | agency
    marketplace_string_id: Mapped[str] = mapped_column(String(32), nullable=False)
    valid_payment_method: Mapped[bool] = mapped_column(Boolean, default=True)
    sub_type: Mapped[str] = mapped_column(String(32), default="")  # KDP_AUTHOR, AMAZON_ATTRIBUTION...
