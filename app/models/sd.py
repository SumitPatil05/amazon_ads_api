from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SDCampaign(Base):
    __tablename__ = "sd_campaigns"

    campaign_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    portfolio_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    tactic: Mapped[str] = mapped_column(String(16), default="T00020")  # T00020 (audiences) | T00030 (contextual)
    budget_type: Mapped[str] = mapped_column(String(16), default="daily")
    budget: Mapped[float] = mapped_column(Float, default=15.0)
    start_date: Mapped[str] = mapped_column(String(16), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cost_type: Mapped[str] = mapped_column(String(16), default="cpc")  # cpc | vcpm

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SDAdGroup(Base):
    __tablename__ = "sd_ad_groups"

    ad_group_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), ForeignKey("sd_campaigns.campaign_id"), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    default_bid: Mapped[float] = mapped_column(Float, default=0.5)
    bid_optimization: Mapped[str] = mapped_column(String(32), default="clicks")  # clicks | conversions | reach

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SDProductAd(Base):
    __tablename__ = "sd_product_ads"

    ad_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    asin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SDTarget(Base):
    __tablename__ = "sd_targets"

    target_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    expression: Mapped[list] = mapped_column(JSON, default=list)
    expression_type: Mapped[str] = mapped_column(String(16), default="MANUAL")
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    bid: Mapped[float] = mapped_column(Float, default=0.5)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
