from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.config import get_settings
from app.db import init_db
from app.routers.portfolios import router as portfolios_router
from app.routers.profiles import router as profiles_router
from app.routers.reports.downloads import router as downloads_router
from app.routers.reports.reports import router as reports_router
from app.routers.sb.ad_groups import router as sb_ad_groups_router
from app.routers.sb.campaigns import router as sb_campaigns_router
from app.routers.sb.creatives import router as sb_creatives_router
from app.routers.sb.keywords import router as sb_keywords_router
from app.routers.sb.targets import router as sb_targets_router
from app.routers.sd.ad_groups import router as sd_ad_groups_router
from app.routers.sd.campaigns import router as sd_campaigns_router
from app.routers.sd.product_ads import router as sd_product_ads_router
from app.routers.sd.targets import router as sd_targets_router
from app.routers.sp.ad_groups import router as sp_ad_groups_router
from app.routers.sp.campaigns import router as sp_campaigns_router
from app.routers.sp.keywords import router as sp_keywords_router
from app.routers.sp.negative_keywords import router as sp_neg_keywords_router
from app.routers.sp.negative_targets import router as sp_neg_targets_router
from app.routers.sp.product_ads import router as sp_product_ads_router
from app.routers.sp.targets import router as sp_targets_router
from app.seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    run_seed()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Amazon Ads API (Mock)",
        description=(
            "A mock of the Amazon Ads API. Mirrors official paths, headers, media types, "
            "and the async report lifecycle so client code can be developed locally and "
            "switched to the real API later by changing only the base URL and credentials."
        ),
        version="1.0.0-mock",
        lifespan=lifespan,
    )

    app.include_router(auth_router)
    app.include_router(profiles_router)
    app.include_router(portfolios_router)

    app.include_router(sp_campaigns_router)
    app.include_router(sp_ad_groups_router)
    app.include_router(sp_keywords_router)
    app.include_router(sp_neg_keywords_router)
    app.include_router(sp_product_ads_router)
    app.include_router(sp_targets_router)
    app.include_router(sp_neg_targets_router)

    app.include_router(sb_campaigns_router)
    app.include_router(sb_ad_groups_router)
    app.include_router(sb_keywords_router)
    app.include_router(sb_targets_router)
    app.include_router(sb_creatives_router)

    app.include_router(sd_campaigns_router)
    app.include_router(sd_ad_groups_router)
    app.include_router(sd_product_ads_router)
    app.include_router(sd_targets_router)

    app.include_router(reports_router)
    app.include_router(downloads_router)

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "name": "amazon-ads-api-mock",
            "version": app.version,
            "docs": f"{settings.PUBLIC_BASE_URL}/docs",
        }

    return app


app = create_app()
