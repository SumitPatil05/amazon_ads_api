from __future__ import annotations

import gzip
import json
import time
from urllib.parse import urlsplit


def test_report_lifecycle_completes_and_downloads(client, scope_headers):
    r = client.post(
        "/reporting/reports",
        headers=scope_headers,
        json={
            "name": "pytest-report",
            "startDate": "2026-04-10",
            "endDate": "2026-04-20",
            "configuration": {
                "adProduct": "SPONSORED_PRODUCTS",
                "groupBy": ["campaign"],
                "columns": [
                    "impressions",
                    "clicks",
                    "cost",
                    "sales1d",
                    "campaignId",
                    "campaignName",
                ],
                "reportTypeId": "spCampaigns",
                "timeUnit": "SUMMARY",
                "format": "GZIP_JSON",
            },
        },
    )
    assert r.status_code == 200
    rid = r.json()["reportId"]
    assert r.json()["status"] in {"PENDING", "PROCESSING"}

    deadline = time.time() + 15
    while time.time() < deadline:
        r = client.get(f"/reporting/reports/{rid}", headers=scope_headers)
        assert r.status_code == 200
        body = r.json()
        if body["status"] in {"COMPLETED", "FAILED"}:
            break
        time.sleep(0.2)
    else:
        raise AssertionError("Report did not reach a terminal state in time")

    assert body["status"] == "COMPLETED", body
    assert body["url"].startswith("http://testserver/downloads/")
    assert body["fileSize"] > 0
    assert body["urlExpiresAt"]

    # Download via the same TestClient so testserver host matches.
    download_path = urlsplit(body["url"]).path
    r = client.get(download_path)
    assert r.status_code == 200
    rows = json.loads(gzip.decompress(r.content))
    assert len(rows) >= 1
    sample = rows[0]
    # Requested columns should be present
    for k in ("impressions", "clicks", "cost", "sales1d", "campaignId", "campaignName"):
        assert k in sample


def test_report_unsupported_type_fails(client, scope_headers):
    r = client.post(
        "/reporting/reports",
        headers=scope_headers,
        json={
            "name": "bad",
            "startDate": "2026-04-10",
            "endDate": "2026-04-20",
            "configuration": {
                "adProduct": "SPONSORED_PRODUCTS",
                "groupBy": [],
                "columns": [],
                "reportTypeId": "noSuchReport",
                "timeUnit": "SUMMARY",
                "format": "GZIP_JSON",
            },
        },
    )
    assert r.status_code == 200
    rid = r.json()["reportId"]

    deadline = time.time() + 10
    while time.time() < deadline:
        r = client.get(f"/reporting/reports/{rid}", headers=scope_headers)
        body = r.json()
        if body["status"] in {"COMPLETED", "FAILED"}:
            break
        time.sleep(0.2)
    assert body["status"] == "FAILED"
    assert "noSuchReport" in (body["failureReason"] or "")


def test_report_download_token_required(client):
    r = client.get("/downloads/garbage-token")
    assert r.status_code == 403
