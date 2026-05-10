from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class SBBidding(BaseModel):
    model_config = ConfigDict(extra="allow")

    bidOptimizeForConversions: bool | None = None
    bidAdjustments: list[dict[str, Any]] | None = None


class SBCampaignCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    state: str = "ENABLED"
    portfolioId: str | None = None
    budgetType: str = "DAILY"  # DAILY | LIFETIME
    budget: float
    startDate: str
    endDate: str | None = None
    bidding: SBBidding | None = None
    brandEntityId: str | None = None


class SBCampaignUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    name: str | None = None
    state: str | None = None
    budget: float | None = None
    bidding: SBBidding | None = None


class SBCampaign(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    name: str
    state: str
    portfolioId: str | None = None
    budgetType: str
    budget: float
    startDate: str
    endDate: str | None = None
    bidding: SBBidding | None = None
    brandEntityId: str | None = None


class SBCampaignList(BaseModel):
    campaigns: list[SBCampaign] = []
    nextToken: str | None = None


class SBAdGroupCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    campaignId: str
    state: str = "ENABLED"


class SBAdGroupUpdate(BaseModel):
    adGroupId: str
    name: str | None = None
    state: str | None = None


class SBAdGroup(BaseModel):
    model_config = ConfigDict(extra="allow")

    adGroupId: str
    campaignId: str
    name: str
    state: str


class SBAdGroupList(BaseModel):
    adGroups: list[SBAdGroup] = []
    nextToken: str | None = None


class SBKeywordCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str
    keywordText: str
    matchType: str = "EXACT"
    bid: float = 1.0
    state: str = "ENABLED"


class SBKeyword(BaseModel):
    model_config = ConfigDict(extra="allow")

    keywordId: str
    campaignId: str
    adGroupId: str
    keywordText: str
    matchType: str
    bid: float
    state: str


class SBKeywordList(BaseModel):
    keywords: list[SBKeyword] = []
    nextToken: str | None = None


class SBTargetExpression(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    value: str | None = None


class SBTargetCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str
    expression: list[SBTargetExpression]
    expressionType: str = "MANUAL"
    bid: float = 1.0
    state: str = "ENABLED"


class SBTarget(BaseModel):
    model_config = ConfigDict(extra="allow")

    targetId: str
    campaignId: str
    adGroupId: str
    expression: list[SBTargetExpression]
    expressionType: str
    bid: float
    state: str


class SBTargetList(BaseModel):
    targets: list[SBTarget] = []
    nextToken: str | None = None


class SBCreativeCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    adGroupId: str
    creativeType: str = "PRODUCT_COLLECTION"  # PRODUCT_COLLECTION | VIDEO | STORE_SPOTLIGHT | BRAND_VIDEO
    headline: str | None = None
    brandName: str | None = None
    brandLogoAssetId: str | None = None
    videoAssetId: str | None = None
    asins: list[str] = []
    state: str = "ENABLED"


class SBCreative(BaseModel):
    model_config = ConfigDict(extra="allow")

    creativeId: str
    adGroupId: str
    campaignId: str
    creativeType: str
    headline: str | None = None
    brandName: str | None = None
    brandLogoAssetId: str | None = None
    videoAssetId: str | None = None
    asins: list[str] = []
    state: str


class SBCreativeList(BaseModel):
    creatives: list[SBCreative] = []
    nextToken: str | None = None
