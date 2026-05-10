from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DynamicBidding(BaseModel):
    model_config = ConfigDict(extra="allow")

    strategy: str | None = None  # LEGACY_FOR_SALES | AUTO_FOR_SALES | RULE_BASED
    placementBidding: list[dict[str, Any]] | None = None


class Budget(BaseModel):
    model_config = ConfigDict(extra="allow")

    budget: float
    budgetType: str = "DAILY"


class CampaignCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str
    state: str = "ENABLED"
    targetingType: str = "MANUAL"
    portfolioId: str | None = None
    dynamicBidding: DynamicBidding | None = None
    budget: Budget | None = None
    dailyBudget: float | None = None
    startDate: str
    endDate: str | None = None
    tags: dict[str, str] | None = None


class CampaignUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    campaignId: str
    name: str | None = None
    state: str | None = None
    portfolioId: str | None = None
    dynamicBidding: DynamicBidding | None = None
    budget: Budget | None = None
    dailyBudget: float | None = None
    startDate: str | None = None
    endDate: str | None = None
    tags: dict[str, str] | None = None


class Campaign(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    campaignId: str
    portfolioId: str | None = None
    name: str
    state: str
    targetingType: str
    dailyBudget: float
    budget: Budget | None = None
    dynamicBidding: DynamicBidding | None = None
    startDate: str
    endDate: str | None = None
    tags: dict[str, str] | None = None


class CampaignList(BaseModel):
    campaigns: list[Campaign] = []
    nextToken: str | None = None


# Ad groups -----------------------------------------------------------------


class AdGroupCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    campaignId: str
    defaultBid: float = 0.75
    state: str = "ENABLED"


class AdGroupUpdate(BaseModel):
    adGroupId: str
    name: str | None = None
    defaultBid: float | None = None
    state: str | None = None


class AdGroup(BaseModel):
    model_config = ConfigDict(extra="allow")

    adGroupId: str
    campaignId: str
    name: str
    defaultBid: float
    state: str


class AdGroupList(BaseModel):
    adGroups: list[AdGroup] = []
    nextToken: str | None = None


# Keywords ------------------------------------------------------------------


class KeywordCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str
    keywordText: str
    matchType: str = "EXACT"  # EXACT | PHRASE | BROAD
    state: str = "ENABLED"
    bid: float = 0.75
    nativeLanguageKeyword: str | None = None
    nativeLanguageLocale: str | None = None


class KeywordUpdate(BaseModel):
    keywordId: str
    state: str | None = None
    bid: float | None = None


class Keyword(BaseModel):
    model_config = ConfigDict(extra="allow")

    keywordId: str
    campaignId: str
    adGroupId: str
    keywordText: str
    matchType: str
    state: str
    bid: float
    nativeLanguageKeyword: str | None = None
    nativeLanguageLocale: str | None = None


class KeywordList(BaseModel):
    keywords: list[Keyword] = []
    nextToken: str | None = None


# Negative keywords ---------------------------------------------------------


class NegativeKeywordCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str | None = None
    keywordText: str
    matchType: str = "NEGATIVE_EXACT"
    state: str = "ENABLED"


class NegativeKeyword(BaseModel):
    model_config = ConfigDict(extra="allow")

    keywordId: str
    campaignId: str
    adGroupId: str | None = None
    keywordText: str
    matchType: str
    state: str


class NegativeKeywordList(BaseModel):
    negativeKeywords: list[NegativeKeyword] = []
    nextToken: str | None = None


# Product ads ---------------------------------------------------------------


class ProductAdCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str
    state: str = "ENABLED"
    asin: str | None = None
    sku: str | None = None


class ProductAdUpdate(BaseModel):
    adId: str
    state: str | None = None


class ProductAd(BaseModel):
    model_config = ConfigDict(extra="allow")

    adId: str
    campaignId: str
    adGroupId: str
    asin: str | None = None
    sku: str | None = None
    state: str


class ProductAdList(BaseModel):
    productAds: list[ProductAd] = []
    nextToken: str | None = None


# Targets -------------------------------------------------------------------


class TargetExpression(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str = Field(alias="type")  # ASIN_SAME_AS, QUERY_HIGH_REL_MATCHES, ASIN_CATEGORY_SAME_AS, etc.
    value: str | None = None


class TargetCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str
    state: str = "ENABLED"
    expression: list[TargetExpression]
    expressionType: str = "MANUAL"
    bid: float = 0.75


class TargetUpdate(BaseModel):
    targetId: str
    state: str | None = None
    bid: float | None = None
    expression: list[TargetExpression] | None = None


class Target(BaseModel):
    model_config = ConfigDict(extra="allow")

    targetId: str
    campaignId: str
    adGroupId: str
    state: str
    expression: list[TargetExpression]
    expressionType: str
    bid: float


class TargetList(BaseModel):
    targetingClauses: list[Target] = []
    nextToken: str | None = None


class NegativeTargetCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str | None = None
    state: str = "ENABLED"
    expression: list[TargetExpression]


class NegativeTarget(BaseModel):
    model_config = ConfigDict(extra="allow")

    targetId: str
    campaignId: str
    adGroupId: str | None = None
    state: str
    expression: list[TargetExpression]


class NegativeTargetList(BaseModel):
    negativeTargetingClauses: list[NegativeTarget] = []
    nextToken: str | None = None
