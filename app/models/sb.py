from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SBCampaign(Base):
    __tablename__ = "sb_campaigns"

    campaign_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    portfolio_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    budget_type: Mapped[str] = mapped_column(String(16), default="DAILY")  # DAILY | LIFETIME
    budget: Mapped[float] = mapped_column(Float, default=20.0)
    start_date: Mapped[str] = mapped_column(String(16), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bidding: Mapped[dict] = mapped_column(JSON, default=dict)
    brand_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SBAdGroup(Base):
    __tablename__ = "sb_ad_groups"

    ad_group_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), ForeignKey("sb_campaigns.campaign_id"), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SBKeyword(Base):
    __tablename__ = "sb_keywords"

    keyword_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    keyword_text: Mapped[str] = mapped_column(String(255), nullable=False)
    match_type: Mapped[str] = mapped_column(String(16), default="EXACT")
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    bid: Mapped[float] = mapped_column(Float, default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SBTarget(Base):
    __tablename__ = "sb_targets"

    target_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    ad_group_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    expression: Mapped[list] = mapped_column(JSON, default=list)
    expression_type: Mapped[str] = mapped_column(String(16), default="MANUAL")
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")
    bid: Mapped[float] = mapped_column(Float, default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SBCreative(Base):
    __tablename__ = "sb_creatives"

    creative_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    ad_group_id: Mapped[str] = mapped_column(String(20), ForeignKey("sb_ad_groups.ad_group_id"), index=True, nullable=False)
    campaign_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    profile_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    creative_type: Mapped[str] = mapped_column(String(32), default="PRODUCT_COLLECTION")  # PRODUCT_COLLECTION | VIDEO | STORE_SPOTLIGHT | BRAND_VIDEO
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand_logo_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    video_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    asins: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(16), default="ENABLED")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
