from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.portfolio import Portfolio
from app.models.profile import Profile
from app.models.sb import SBAdGroup, SBCampaign, SBCreative, SBKeyword, SBTarget
from app.models.sd import SDAdGroup, SDCampaign, SDProductAd, SDTarget
from app.models.sp import (
    SPAdGroup,
    SPCampaign,
    SPKeyword,
    SPNegativeKeyword,
    SPProductAd,
    SPTarget,
)
from app.services.ids import numeric_id

log = logging.getLogger(__name__)

SEED_ASINS = [
    "B0CXYZ0001",
    "B0CXYZ0002",
    "B0CXYZ0003",
    "B0CXYZ0004",
    "B0CXYZ0005",
    "B0CXYZ0006",
    "B0CXYZ0007",
    "B0CXYZ0008",
]

SEED_KEYWORDS = [
    "wireless earbuds",
    "running shoes",
    "yoga mat",
    "kitchen knife set",
    "stainless water bottle",
    "office chair",
    "laptop stand",
    "garden tools",
]


def _profiles_seed() -> list[dict]:
    return [
        {
            "profile_id": "100000000000001",
            "country_code": "US",
            "currency_code": "USD",
            "timezone": "America/Los_Angeles",
            "marketplace_string_id": "ATVPDKIKX0DER",
            "account_id": "ENTITY1ABCDEFG",
            "account_name": "Demo US Seller",
            "account_type": "seller",
            "sub_type": "",
        },
        {
            "profile_id": "100000000000002",
            "country_code": "GB",
            "currency_code": "GBP",
            "timezone": "Europe/London",
            "marketplace_string_id": "A1F83G8C2ARO7P",
            "account_id": "ENTITY2HIJKLMN",
            "account_name": "Demo UK Vendor",
            "account_type": "vendor",
            "sub_type": "VENDOR_GROUP",
        },
        {
            "profile_id": "100000000000003",
            "country_code": "DE",
            "currency_code": "EUR",
            "timezone": "Europe/Berlin",
            "marketplace_string_id": "A1PA6795UKMFR9",
            "account_id": "ENTITY3OPQRSTU",
            "account_name": "Demo DE Seller",
            "account_type": "seller",
            "sub_type": "",
        },
    ]


def _create_portfolios(db: Session, profile_id: str, currency: str) -> list[Portfolio]:
    items = []
    for name, budget in [("Brand Launch", 1500.0), ("Always-On", 2500.0)]:
        p = Portfolio(
            portfolio_id=numeric_id(11),
            profile_id=profile_id,
            name=name,
            state="enabled",
            in_budget=True,
            budget_amount=budget,
            budget_currency_code=currency,
            budget_policy="dateRange",
            budget_start_date=datetime.utcnow().date().isoformat(),
            budget_end_date=(datetime.utcnow() + timedelta(days=90)).date().isoformat(),
        )
        db.add(p)
        items.append(p)
    return items


def _create_sp(db: Session, profile_id: str, portfolio_ids: Iterable[str]) -> None:
    rng = random.Random(profile_id)
    portfolio_list = list(portfolio_ids)

    for ci in range(5):
        targeting = "AUTO" if ci % 3 == 0 else "MANUAL"
        c = SPCampaign(
            campaign_id=numeric_id(11),
            profile_id=profile_id,
            portfolio_id=rng.choice(portfolio_list),
            name=f"SP-Campaign-{ci+1}",
            state="ENABLED",
            targeting_type=targeting,
            daily_budget=round(rng.uniform(10, 80), 2),
            start_date=datetime.utcnow().date().isoformat(),
            end_date=None,
            dynamic_bidding={"strategy": rng.choice(["LEGACY_FOR_SALES", "AUTO_FOR_SALES", "RULE_BASED"])},
            tags={"team": "demo"},
        )
        db.add(c)
        db.flush()

        for ag_i in range(2):
            ag = SPAdGroup(
                ad_group_id=numeric_id(11),
                campaign_id=c.campaign_id,
                profile_id=profile_id,
                name=f"{c.name}-AG-{ag_i+1}",
                state="ENABLED",
                default_bid=round(rng.uniform(0.3, 1.5), 2),
            )
            db.add(ag)
            db.flush()

            if targeting == "MANUAL":
                for kw in rng.sample(SEED_KEYWORDS, k=5):
                    db.add(
                        SPKeyword(
                            keyword_id=numeric_id(11),
                            campaign_id=c.campaign_id,
                            ad_group_id=ag.ad_group_id,
                            profile_id=profile_id,
                            keyword_text=kw,
                            match_type=rng.choice(["EXACT", "PHRASE", "BROAD"]),
                            state="ENABLED",
                            bid=round(rng.uniform(0.3, 1.8), 2),
                        )
                    )
                # Negative keyword
                db.add(
                    SPNegativeKeyword(
                        keyword_id=numeric_id(11),
                        campaign_id=c.campaign_id,
                        ad_group_id=ag.ad_group_id,
                        profile_id=profile_id,
                        keyword_text="cheap",
                        match_type="NEGATIVE_PHRASE",
                        state="ENABLED",
                    )
                )
            else:
                # AUTO target groups
                for expr in [
                    {"type": "QUERY_BROAD_REL_MATCHES"},
                    {"type": "QUERY_HIGH_REL_MATCHES"},
                    {"type": "ASIN_SUBSTITUTE_RELATED"},
                ]:
                    db.add(
                        SPTarget(
                            target_id=numeric_id(11),
                            campaign_id=c.campaign_id,
                            ad_group_id=ag.ad_group_id,
                            profile_id=profile_id,
                            expression=[expr],
                            expression_type="AUTO",
                            state="ENABLED",
                            bid=round(rng.uniform(0.3, 1.5), 2),
                        )
                    )

            for asin in rng.sample(SEED_ASINS, k=3):
                db.add(
                    SPProductAd(
                        ad_id=numeric_id(11),
                        campaign_id=c.campaign_id,
                        ad_group_id=ag.ad_group_id,
                        profile_id=profile_id,
                        asin=asin,
                        sku=None,
                        state="ENABLED",
                    )
                )


def _create_sb(db: Session, profile_id: str, portfolio_ids: Iterable[str]) -> None:
    rng = random.Random(profile_id + "sb")
    pids = list(portfolio_ids)
    for ci in range(3):
        c = SBCampaign(
            campaign_id=numeric_id(11),
            profile_id=profile_id,
            portfolio_id=rng.choice(pids),
            name=f"SB-Campaign-{ci+1}",
            state="ENABLED",
            budget_type="DAILY",
            budget=round(rng.uniform(20, 120), 2),
            start_date=datetime.utcnow().date().isoformat(),
            end_date=None,
            bidding={"bidOptimizeForConversions": True},
            brand_entity_id="ENTITY-BRAND-001",
        )
        db.add(c)
        db.flush()
        ag = SBAdGroup(
            ad_group_id=numeric_id(11),
            campaign_id=c.campaign_id,
            profile_id=profile_id,
            name=f"{c.name}-AG-1",
            state="ENABLED",
        )
        db.add(ag)
        db.flush()
        db.add(
            SBCreative(
                creative_id="amzn1.assetlibrary.asset1." + numeric_id(8),
                ad_group_id=ag.ad_group_id,
                campaign_id=c.campaign_id,
                profile_id=profile_id,
                creative_type="PRODUCT_COLLECTION",
                headline="Discover our brand",
                brand_name="Demo Brand",
                asins=rng.sample(SEED_ASINS, k=3),
                state="ENABLED",
            )
        )
        for kw in rng.sample(SEED_KEYWORDS, k=4):
            db.add(
                SBKeyword(
                    keyword_id=numeric_id(11),
                    campaign_id=c.campaign_id,
                    ad_group_id=ag.ad_group_id,
                    profile_id=profile_id,
                    keyword_text=kw,
                    match_type=rng.choice(["EXACT", "PHRASE", "BROAD"]),
                    state="ENABLED",
                    bid=round(rng.uniform(0.5, 2.5), 2),
                )
            )
        db.add(
            SBTarget(
                target_id=numeric_id(11),
                campaign_id=c.campaign_id,
                ad_group_id=ag.ad_group_id,
                profile_id=profile_id,
                expression=[{"type": "ASIN_CATEGORY_SAME_AS", "value": "172282"}],
                expression_type="MANUAL",
                state="ENABLED",
                bid=1.25,
            )
        )


def _create_sd(db: Session, profile_id: str, portfolio_ids: Iterable[str]) -> None:
    rng = random.Random(profile_id + "sd")
    pids = list(portfolio_ids)
    for ci in range(2):
        c = SDCampaign(
            campaign_id=numeric_id(11),
            profile_id=profile_id,
            portfolio_id=rng.choice(pids),
            name=f"SD-Campaign-{ci+1}",
            state="ENABLED",
            tactic=rng.choice(["T00020", "T00030"]),
            budget_type="daily",
            budget=round(rng.uniform(15, 60), 2),
            start_date=datetime.utcnow().date().isoformat(),
            end_date=None,
            cost_type="cpc",
        )
        db.add(c)
        db.flush()
        ag = SDAdGroup(
            ad_group_id=numeric_id(11),
            campaign_id=c.campaign_id,
            profile_id=profile_id,
            name=f"{c.name}-AG-1",
            state="ENABLED",
            default_bid=round(rng.uniform(0.4, 1.2), 2),
            bid_optimization=rng.choice(["clicks", "conversions", "reach"]),
        )
        db.add(ag)
        db.flush()
        for asin in rng.sample(SEED_ASINS, k=4):
            db.add(
                SDProductAd(
                    ad_id=numeric_id(11),
                    campaign_id=c.campaign_id,
                    ad_group_id=ag.ad_group_id,
                    profile_id=profile_id,
                    asin=asin,
                    sku=None,
                    state="ENABLED",
                )
            )
        db.add(
            SDTarget(
                target_id=numeric_id(11),
                campaign_id=c.campaign_id,
                ad_group_id=ag.ad_group_id,
                profile_id=profile_id,
                expression=[{"type": "audience", "value": "lookback=30"}],
                expression_type="MANUAL",
                state="ENABLED",
                bid=round(rng.uniform(0.4, 1.5), 2),
            )
        )


def run_seed() -> None:
    with SessionLocal() as db:
        # Idempotent: skip if any profile already exists.
        if db.query(Profile).count() > 0:
            log.info("Seed skipped (profiles already exist)")
            return

        for prof in _profiles_seed():
            db.add(Profile(**prof, daily_budget=0.0, valid_payment_method=True))
        db.commit()

        for prof in db.query(Profile).all():
            portfolios = _create_portfolios(db, prof.profile_id, prof.currency_code)
            db.commit()
            pids = [p.portfolio_id for p in portfolios]
            _create_sp(db, prof.profile_id, pids)
            _create_sb(db, prof.profile_id, pids)
            _create_sd(db, prof.profile_id, pids)
            db.commit()

        log.info("Seed complete")
