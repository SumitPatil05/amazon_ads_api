from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class CamelModel(BaseModel):
    """Base for response models that mirror Amazon's camelCase shape."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class StateFilter(BaseModel):
    include: list[str] | None = None


class IdFilter(BaseModel):
    include: list[str] | None = None


class ListRequest(BaseModel):
    """Common request envelope used by Amazon Ads v3 list endpoints."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    nextToken: str | None = None
    maxResults: int | None = Field(default=None, ge=1, le=1000)
    stateFilter: StateFilter | None = None
    campaignIdFilter: IdFilter | None = None
    adGroupIdFilter: IdFilter | None = None
    portfolioIdFilter: IdFilter | None = None
    keywordIdFilter: IdFilter | None = None
    adIdFilter: IdFilter | None = None
    targetIdFilter: IdFilter | None = None
    nameFilter: dict[str, Any] | None = None


class BatchSuccessItem(BaseModel):
    index: int
    id: str = Field(alias="id")


class BatchErrorItem(BaseModel):
    index: int
    code: str
    details: str


class BatchResponse(BaseModel, Generic[T]):
    success: list[T] = []
    error: list[BatchErrorItem] = []
