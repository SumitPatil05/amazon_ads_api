from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SDCampaignCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    tactic: str = "T00020"  # T00020 | T00030
    state: str = "ENABLED"
    portfolioId: str | None = None
    budgetType: str = "daily"
    budget: float = 15.0
    startDate: str
    endDate: str | None = None
    costType: str = "cpc"  # cpc | vcpm


class SDCampaignUpdate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    name: str | None = None
    state: str | None = None
    budget: float | None = None


class SDCampaign(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    name: str
    tactic: str
    state: str
    portfolioId: str | None = None
    budgetType: str
    budget: float
    startDate: str
    endDate: str | None = None
    costType: str


class SDCampaignList(BaseModel):
    campaigns: list[SDCampaign] = []
    nextToken: str | None = None


class SDAdGroupCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    campaignId: str
    state: str = "ENABLED"
    defaultBid: float = 0.5
    bidOptimization: str = "clicks"


class SDAdGroupUpdate(BaseModel):
    adGroupId: str
    name: str | None = None
    state: str | None = None
    defaultBid: float | None = None


class SDAdGroup(BaseModel):
    model_config = ConfigDict(extra="allow")

    adGroupId: str
    campaignId: str
    name: str
    state: str
    defaultBid: float
    bidOptimization: str


class SDAdGroupList(BaseModel):
    adGroups: list[SDAdGroup] = []
    nextToken: str | None = None


class SDProductAdCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str
    state: str = "ENABLED"
    asin: str | None = None
    sku: str | None = None


class SDProductAd(BaseModel):
    model_config = ConfigDict(extra="allow")

    adId: str
    campaignId: str
    adGroupId: str
    state: str
    asin: str | None = None
    sku: str | None = None


class SDProductAdList(BaseModel):
    productAds: list[SDProductAd] = []
    nextToken: str | None = None


class SDTargetExpression(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    value: str | None = None


class SDTargetCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    campaignId: str
    adGroupId: str
    expression: list[SDTargetExpression]
    expressionType: str = "MANUAL"
    state: str = "ENABLED"
    bid: float = 0.5


class SDTarget(BaseModel):
    model_config = ConfigDict(extra="allow")

    targetId: str
    campaignId: str
    adGroupId: str
    expression: list[SDTargetExpression]
    expressionType: str
    state: str
    bid: float


class SDTargetList(BaseModel):
    targets: list[SDTarget] = []
    nextToken: str | None = None
