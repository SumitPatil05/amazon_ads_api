from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    adProduct: str  # SPONSORED_PRODUCTS | SPONSORED_BRANDS | SPONSORED_DISPLAY
    groupBy: list[str] = []
    columns: list[str] = []
    filters: list[dict[str, Any]] | None = None
    reportTypeId: str
    timeUnit: str = "SUMMARY"  # DAILY | SUMMARY
    format: str = "GZIP_JSON"  # GZIP_JSON


class CreateAsyncReportRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    startDate: str
    endDate: str
    configuration: ReportConfiguration


class AsyncReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    reportId: str
    status: str  # PENDING | PROCESSING | COMPLETED | FAILED
    statusDetails: str | None = None
    failureReason: str | None = None
    name: str | None = None
    startDate: str
    endDate: str
    configuration: ReportConfiguration
    url: str | None = None
    urlExpiresAt: str | None = None
    fileSize: int | None = None
    format: str = "GZIP_JSON"
    createdAt: str | None = None
    updatedAt: str | None = None
