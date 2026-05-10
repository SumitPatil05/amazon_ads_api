from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def app_with_temp_db():
    """Boot a clean app with an isolated SQLite db + storage dir for the test run."""
    tmpdir = tempfile.mkdtemp(prefix="ads-mock-test-")
    db_path = os.path.join(tmpdir, "mock.db")
    storage_path = os.path.join(tmpdir, "reports")
    Path(storage_path).mkdir(parents=True, exist_ok=True)

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["REPORTS_STORAGE_DIR"] = storage_path
    os.environ["LWA_JWT_SECRET"] = "test-secret"
    os.environ["REPORT_MIN_DELAY_SEC"] = "0.1"
    os.environ["REPORT_MAX_DELAY_SEC"] = "0.3"
    os.environ["DOWNLOAD_URL_TTL_SEC"] = "300"
    os.environ["PUBLIC_BASE_URL"] = "http://testserver"

    # Reset cached settings, then build app fresh.
    from app.config import get_settings

    get_settings.cache_clear()

    from app import db as db_module

    # Rebuild the engine pointing at the temp db.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_module.engine.dispose()
    db_module.engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True
    )
    db_module.SessionLocal = sessionmaker(
        bind=db_module.engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    # Create schema and seed.
    from app.db import init_db
    from app.seed import run_seed

    init_db()
    run_seed()

    from app.main import create_app

    app = create_app()
    yield app
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture()
def client(app_with_temp_db):
    from fastapi.testclient import TestClient

    # Use TestClient as a normal context-manager so lifespan runs once.
    with TestClient(app_with_temp_db) as c:
        yield c


@pytest.fixture()
def auth_headers(client) -> dict:
    r = client.post(
        "/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": "Atzr|test",
            "client_id": "amzn1.application-oa2-client.test",
            "client_secret": "test-secret",
        },
    )
    assert r.status_code == 200, r.text
    return {
        "Authorization": f"Bearer {r.json()['access_token']}",
        "Amazon-Advertising-API-ClientId": "amzn1.application-oa2-client.test",
    }


@pytest.fixture()
def profile_id(client, auth_headers) -> str:
    r = client.get("/v2/profiles", headers=auth_headers)
    assert r.status_code == 200
    return str(r.json()[0]["profileId"])


@pytest.fixture()
def scope_headers(auth_headers, profile_id) -> dict:
    return {**auth_headers, "Amazon-Advertising-API-Scope": profile_id}
