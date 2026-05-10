"""Synthesises deterministic Amazon Ads reports from seeded entities.

The generator hydrates rows for a (profile, ad product, report type, date range)
tuple. Metrics are seeded by (entity_id, date) so the same query produces the
same numbers across runs - useful for client-side regression tests.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.sb import SBAdGroup, SBCampaign, SBKeyword
from app.models.sd import SDAdGroup, SDCampaign, SDProductAd
from app.models.sp import SPAdGroup, SPCampaign, SPKeyword, SPProductAd

# --- helpers ---------------------------------------------------------------


def _seeded_rng(*parts: str) -> random.Random:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _date_range(start: str, end: str) -> list[date]:
    s = datetime.strptime(start, "%Y-%m-%d").date()
    e = datetime.strptime(end, "%Y-%m-%d").date()
    if e < s:
        return []
    return [s + timedelta(days=i) for i in range((e - s).days + 1)]


def _metrics_for(rng: random.Random, *, has_clicks: bool = True) -> dict[str, float]:
    impressions = rng.randint(50, 8000)
    ctr = rng.uniform(0.002, 0.05)
    clicks = max(0, int(impressions * ctr))
    cpc = round(rng.uniform(0.15, 2.5), 2)
    cost = round(clicks * cpc, 2)
    conv_rate = rng.uniform(0.02, 0.18)
    purchases = max(0, int(clicks * conv_rate))
    aov = rng.uniform(15.0, 80.0)
    sales = round(purchases * aov, 2)
    out: dict[str, float] = {
        "impressions": impressions,
        "clicks": clicks if has_clicks else 0,
        "cost": cost,
        "costPerClick": cpc if clicks else 0.0,
        "clickThroughRate": round(ctr, 6),
        "purchases1d": purchases,
        "purchases7d": purchases + max(0, int(purchases * 0.2)),
        "purchases14d": purchases + max(0, int(purchases * 0.35)),
        "purchases30d": purchases + max(0, int(purchases * 0.5)),
        "sales1d": sales,
        "sales7d": round(sales * 1.2, 2),
        "sales14d": round(sales * 1.35, 2),
        "sales30d": round(sales * 1.5, 2),
        "unitsSoldClicks1d": purchases,
        "unitsSoldClicks7d": purchases + max(0, int(purchases * 0.2)),
        "unitsSoldClicks14d": purchases + max(0, int(purchases * 0.35)),
        "unitsSoldClicks30d": purchases + max(0, int(purchases * 0.5)),
        "acosClicks7d": round((cost / max(sales * 1.2, 0.01)) * 100, 2) if sales else 0.0,
        "roasClicks7d": round((sales * 1.2) / max(cost, 0.01), 4) if cost else 0.0,
    }
    return out


def _select_columns(row: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    if not columns:
        return row
    return {c: row.get(c) for c in columns}


# --- generators per report type -------------------------------------------


def _sp_campaigns(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    campaigns = db.query(SPCampaign).filter(SPCampaign.profile_id == profile_id).all()
    for c in campaigns:
        if time_unit.upper() == "SUMMARY":
            rng = _seeded_rng(rng_seed, c.campaign_id, "summary")
            base = _metrics_for(rng)
            base["campaignId"] = c.campaign_id
            base["campaignName"] = c.name
            base["campaignStatus"] = c.state
            base["campaignBudgetType"] = "DAILY"
            base["campaignBudgetAmount"] = c.daily_budget
            base["startDate"] = dates[0].isoformat() if dates else None
            base["endDate"] = dates[-1].isoformat() if dates else None
            rows.append(base)
        else:
            for d in dates:
                rng = _seeded_rng(rng_seed, c.campaign_id, d.isoformat())
                base = _metrics_for(rng)
                base["date"] = d.isoformat()
                base["campaignId"] = c.campaign_id
                base["campaignName"] = c.name
                base["campaignStatus"] = c.state
                rows.append(base)
    return rows


def _sp_advertised_product(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ads = db.query(SPProductAd).filter(SPProductAd.profile_id == profile_id).all()
    for a in ads:
        keys = [(d, _seeded_rng(rng_seed, a.ad_id, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, a.ad_id, "summary"))]
        for d, rng in keys:
            row = _metrics_for(rng)
            if d is not None:
                row["date"] = d.isoformat()
            row["adId"] = a.ad_id
            row["campaignId"] = a.campaign_id
            row["adGroupId"] = a.ad_group_id
            row["advertisedAsin"] = a.asin
            row["advertisedSku"] = a.sku
            rows.append(row)
    return rows


def _sp_search_term(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    keywords = db.query(SPKeyword).filter(SPKeyword.profile_id == profile_id).all()
    for k in keywords:
        # Generate a couple of search-term variants per keyword.
        variants = [k.keyword_text, k.keyword_text + " best", k.keyword_text + " amazon"]
        for st in variants:
            keys = [(d, _seeded_rng(rng_seed, k.keyword_id, st, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, k.keyword_id, st, "summary"))]
            for d, rng in keys:
                row = _metrics_for(rng)
                if d is not None:
                    row["date"] = d.isoformat()
                row["keywordId"] = k.keyword_id
                row["keyword"] = k.keyword_text
                row["matchType"] = k.match_type
                row["searchTerm"] = st
                row["campaignId"] = k.campaign_id
                row["adGroupId"] = k.ad_group_id
                rows.append(row)
    return rows


def _sp_targeting(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    keywords = db.query(SPKeyword).filter(SPKeyword.profile_id == profile_id).all()
    for k in keywords:
        keys = [(d, _seeded_rng(rng_seed, k.keyword_id, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, k.keyword_id, "summary"))]
        for d, rng in keys:
            row = _metrics_for(rng)
            if d is not None:
                row["date"] = d.isoformat()
            row["keywordId"] = k.keyword_id
            row["keyword"] = k.keyword_text
            row["matchType"] = k.match_type
            row["bid"] = k.bid
            row["campaignId"] = k.campaign_id
            row["adGroupId"] = k.ad_group_id
            row["targetingType"] = "TARGETING_EXPRESSION"
            rows.append(row)
    return rows


def _sb_campaigns(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    campaigns = db.query(SBCampaign).filter(SBCampaign.profile_id == profile_id).all()
    for c in campaigns:
        keys = [(d, _seeded_rng(rng_seed, c.campaign_id, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, c.campaign_id, "summary"))]
        for d, rng in keys:
            row = _metrics_for(rng)
            if d is not None:
                row["date"] = d.isoformat()
            row["campaignId"] = c.campaign_id
            row["campaignName"] = c.name
            row["campaignStatus"] = c.state
            row["campaignBudgetAmount"] = c.budget
            row["campaignBudgetType"] = c.budget_type
            rows.append(row)
    return rows


def _sb_ad_group(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = db.query(SBAdGroup).filter(SBAdGroup.profile_id == profile_id).all()
    for g in groups:
        keys = [(d, _seeded_rng(rng_seed, g.ad_group_id, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, g.ad_group_id, "summary"))]
        for d, rng in keys:
            row = _metrics_for(rng)
            if d is not None:
                row["date"] = d.isoformat()
            row["adGroupId"] = g.ad_group_id
            row["adGroupName"] = g.name
            row["campaignId"] = g.campaign_id
            rows.append(row)
    return rows


def _sb_keyword(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    keywords = db.query(SBKeyword).filter(SBKeyword.profile_id == profile_id).all()
    for k in keywords:
        keys = [(d, _seeded_rng(rng_seed, k.keyword_id, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, k.keyword_id, "summary"))]
        for d, rng in keys:
            row = _metrics_for(rng)
            if d is not None:
                row["date"] = d.isoformat()
            row["keywordId"] = k.keyword_id
            row["keyword"] = k.keyword_text
            row["matchType"] = k.match_type
            row["bid"] = k.bid
            row["campaignId"] = k.campaign_id
            row["adGroupId"] = k.ad_group_id
            rows.append(row)
    return rows


def _sd_campaigns(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    campaigns = db.query(SDCampaign).filter(SDCampaign.profile_id == profile_id).all()
    for c in campaigns:
        keys = [(d, _seeded_rng(rng_seed, c.campaign_id, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, c.campaign_id, "summary"))]
        for d, rng in keys:
            row = _metrics_for(rng)
            if d is not None:
                row["date"] = d.isoformat()
            row["campaignId"] = c.campaign_id
            row["campaignName"] = c.name
            row["tactic"] = c.tactic
            row["costType"] = c.cost_type
            rows.append(row)
    return rows


def _sd_advertised_product(db: Session, profile_id: str, dates: list[date], time_unit: str, rng_seed: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ads = db.query(SDProductAd).filter(SDProductAd.profile_id == profile_id).all()
    for a in ads:
        keys = [(d, _seeded_rng(rng_seed, a.ad_id, d.isoformat())) for d in dates] if time_unit.upper() == "DAILY" else [(None, _seeded_rng(rng_seed, a.ad_id, "summary"))]
        for d, rng in keys:
            row = _metrics_for(rng)
            if d is not None:
                row["date"] = d.isoformat()
            row["adId"] = a.ad_id
            row["advertisedAsin"] = a.asin
            row["campaignId"] = a.campaign_id
            row["adGroupId"] = a.ad_group_id
            rows.append(row)
    return rows


_REPORT_TYPES = {
    "spCampaigns": _sp_campaigns,
    "spAdvertisedProduct": _sp_advertised_product,
    "spSearchTerm": _sp_search_term,
    "spTargeting": _sp_targeting,
    "sbCampaigns": _sb_campaigns,
    "sbAdGroup": _sb_ad_group,
    "sbKeyword": _sb_keyword,
    "sdCampaigns": _sd_campaigns,
    "sdAdvertisedProduct": _sd_advertised_product,
}


def supported_report_types() -> list[str]:
    return sorted(_REPORT_TYPES.keys())


def generate_report_payload(
    db: Session,
    *,
    profile_id: str,
    report_id: str,
    start_date: str,
    end_date: str,
    configuration: dict[str, Any],
) -> list[dict[str, Any]]:
    report_type_id = configuration.get("reportTypeId") or ""
    columns = list(configuration.get("columns") or [])
    time_unit = configuration.get("timeUnit") or "SUMMARY"

    fn = _REPORT_TYPES.get(report_type_id)
    if fn is None:
        raise ValueError(f"Unsupported reportTypeId: {report_type_id}")

    dates = _date_range(start_date, end_date)
    rows = fn(db, profile_id, dates, time_unit, report_id)
    if columns:
        rows = [_select_columns(r, columns) for r in rows]
    return rows


def write_gzip_payload(report_id: str, rows: list[dict[str, Any]]) -> tuple[str, int]:
    settings = get_settings()
    Path(settings.REPORTS_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    fname = os.path.join(settings.REPORTS_STORAGE_DIR, f"{_safe_filename(report_id)}.json.gz")
    payload = json.dumps(rows, separators=(",", ":")).encode("utf-8")
    with gzip.open(fname, "wb") as f:
        f.write(payload)
    return fname, os.path.getsize(fname)


def _safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-._" else "_" for c in s)
