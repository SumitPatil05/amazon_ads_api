from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AccountInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    marketplaceStringId: str
    id: str
    type: str  # seller | vendor | agency
    name: str
    subType: str | None = None
    validPaymentMethod: bool = True


class Profile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    profileId: int
    countryCode: str
    currencyCode: str
    timezone: str = Field(alias="timezone")
    dailyBudget: float = 0.0
    accountInfo: AccountInfo
