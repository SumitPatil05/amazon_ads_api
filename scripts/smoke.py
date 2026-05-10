from __future__ import annotations

import gzip
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8081"


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        # 1. Token
        r = c.post(
            "/auth/o2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "Atzr|mock",
                "client_id": "amzn1.application-oa2-client.demo",
                "client_secret": "demo",
            },
        )
        r.raise_for_status()
        tok = r.json()
        access = tok["access_token"]
        client_id = "amzn1.application-oa2-client.demo"
        auth = {"Authorization": f"Bearer {access}", "Amazon-Advertising-API-ClientId": client_id}
        print("token: OK")

        # 2. Profiles
        r = c.get("/v2/profiles", headers=auth)
        r.raise_for_status()
        profiles = r.json()
        prof_id = str(profiles[0]["profileId"])
        print(f"profiles: {len(profiles)} (using {prof_id})")
        scope = {**auth, "Amazon-Advertising-API-Scope": prof_id}

        # 3. SP roundtrip
        r = c.post("/sp/campaigns/list", json={}, headers=scope)
        r.raise_for_status()
        n_seed = len(r.json()["campaigns"])
        print(f"sp.list (seeded): {n_seed}")

        r = c.post(
            "/sp/campaigns",
            headers=scope,
            json={
                "campaigns": [
                    {
                        "name": "smoke-test-campaign",
                        "targetingType": "MANUAL",
                        "state": "ENABLED",
                        "dailyBudget": 12.50,
                        "startDate": "2026-05-10",
                    }
                ]
            },
        )
        r.raise_for_status()
        created = r.json()["campaigns"]["success"][0]
        cid = created["campaignId"]
        print(f"sp.create: {cid}")

        r = c.post(
            "/sp/campaigns",
            headers=scope,
            json={"campaigns": [{"campaignId": cid, "state": "PAUSED", "dailyBudget": 17.0}]},
        )
        # update uses PUT
        r = c.put(
            "/sp/campaigns",
            headers=scope,
            json={"campaigns": [{"campaignId": cid, "state": "PAUSED", "dailyBudget": 17.0}]},
        )
        r.raise_for_status()
        print(f"sp.update -> {r.json()['campaigns']['success'][0]['campaign']['state']}")

        r = c.delete(f"/sp/campaigns/{cid}", headers=scope)
        r.raise_for_status()
        print("sp.delete: OK")

        # 4. Reports
        r = c.post(
            "/reporting/reports",
            headers=scope,
            json={
                "name": "smoke-sp",
                "startDate": "2026-04-10",
                "endDate": "2026-05-09",
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
        r.raise_for_status()
        report = r.json()
        rid = report["reportId"]
        print(f"report.create: {rid} ({report['status']})")

        deadline = time.time() + 30
        while time.time() < deadline:
            r = c.get(f"/reporting/reports/{rid}", headers=scope)
            r.raise_for_status()
            j = r.json()
            if j["status"] in ("COMPLETED", "FAILED"):
                break
            time.sleep(1)
        else:
            print("TIMEOUT waiting for report", file=sys.stderr)
            return 1

        if j["status"] != "COMPLETED":
            print("FAIL", j)
            return 1
        print(f"report.completed: rows file size = {j['fileSize']} bytes")

        url = j["url"].replace("http://localhost:8080", BASE)
        r = c.get(url)
        r.raise_for_status()
        rows = json.loads(gzip.decompress(r.content))
        print(f"download.gunzip: {len(rows)} rows; first row keys = {sorted(rows[0].keys())[:8] if rows else []}")

    print("\nALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
