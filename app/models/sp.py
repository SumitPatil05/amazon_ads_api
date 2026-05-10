from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SPCampaign(Base):
    __tablename__ = "sp_campaigns"

    campaign_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    portfolio_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")  # ENABLED | PAUSED | ARCHIVED
    targeting_type: Mapped[str] = mapped_column(String(16), default="MANUAL")  # AUTO | MANUAL

    daily_budget: Mapped[float] = mapped_column(Float, default=10.0)
    start_date: Mapped[str] = mapped_column(String(16), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(16), nullable=True)

    dynamic_bidding: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SPAdGroup(Base):
    __tablename__ = "sp_ad_groups"

    ad_group_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), ForeignKey("sp_campaigns.campaign_id"), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    default_bid: Mapped[float] = mapped_column(Float, default=0.75)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SPKeyword(Base):
    __tablename__ = "sp_keywords"

    keyword_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str] = mapped_column(String(20), ForeignKey("sp_ad_groups.ad_group_id"), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    keyword_text: Mapped[str] = mapped_column(String(255), nullable=False)
    native_language_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    native_language_locale: Mapped[str | None] = mapped_column(String(16), nullable=True)
    match_type: Mapped[str] = mapped_column(String(16), default="EXACT")  # EXACT | PHRASE | BROAD
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    bid: Mapped[float] = mapped_column(Float, default=0.75)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SPNegativeKeyword(Base):
    __tablename__ = "sp_negative_keywords"

    keyword_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    keyword_text: Mapped[str] = mapped_column(String(255), nullable=False)
    match_type: Mapped[str] = mapped_column(String(32), default="NEGATIVE_EXACT")  # NEGATIVE_EXACT | NEGATIVE_PHRASE
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SPProductAd(Base):
    __tablename__ = "sp_product_ads"

    ad_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    asin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SPTarget(Base):
    __tablename__ = "sp_targets"

    target_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    expression: Mapped[list] = mapped_column(JSON, default=list)
    expression_type: Mapped[str] = mapped_column(String(16), default="MANUAL")  # AUTO | MANUAL
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    bid: Mapped[float] = mapped_column(Float, default=0.75)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SPNegativeTarget(Base):
    __tablename__ = "sp_negative_targets"

    target_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    expression: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
