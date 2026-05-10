from __future__ import annotations


def test_sb_campaigns_list_and_create(client, scope_headers):
    r = client.post("/sb/v4/campaigns/list", json={}, headers=scope_headers)
    assert r.status_code == 200
    assert len(r.json()["campaigns"]) >= 1

    r = client.post(
        "/sb/v4/campaigns",
        headers=scope_headers,
        json={
            "campaigns": [
                {
                    "name": "pytest-sb-campaign",
                    "state": "ENABLED",
                    "budgetType": "DAILY",
                    "budget": 30.0,
                    "startDate": "2026-05-10",
                }
            ]
        },
    )
    assert r.status_code == 207
    assert r.json()["campaigns"]["success"][0]["campaign"]["budget"] == 30.0


def test_sd_campaigns_list_and_targets(client, scope_headers):
    r = client.post("/sd/campaigns/list", json={}, headers=scope_headers)
    assert r.status_code == 200
    assert len(r.json()["campaigns"]) >= 1

    r = client.post("/sd/targets/list", json={}, headers=scope_headers)
    assert r.status_code == 200
    assert isinstance(r.json()["targets"], list)
