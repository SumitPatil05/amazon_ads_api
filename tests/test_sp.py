from __future__ import annotations


def test_sp_campaign_roundtrip(client, scope_headers):
    # 1. List existing
    r = client.post("/sp/campaigns/list", json={}, headers=scope_headers)
    assert r.status_code == 200
    seeded = r.json()["campaigns"]
    assert len(seeded) >= 1
    assert {"campaignId", "name", "state", "targetingType", "dailyBudget"} <= set(seeded[0].keys())

    # 2. Create a new campaign
    r = client.post(
        "/sp/campaigns",
        headers=scope_headers,
        json={
            "campaigns": [
                {
                    "name": "pytest-campaign",
                    "targetingType": "MANUAL",
                    "state": "ENABLED",
                    "dailyBudget": 12.34,
                    "startDate": "2026-05-10",
                }
            ]
        },
    )
    assert r.status_code == 207, r.text
    success = r.json()["campaigns"]["success"]
    assert len(success) == 1
    cid = success[0]["campaignId"]

    # 3. List filtered to our new campaign
    r = client.post(
        "/sp/campaigns/list",
        json={"campaignIdFilter": {"include": [cid]}},
        headers=scope_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["campaigns"]) == 1
    assert r.json()["campaigns"][0]["dailyBudget"] == 12.34

    # 4. Update via PUT
    r = client.put(
        "/sp/campaigns",
        headers=scope_headers,
        json={"campaigns": [{"campaignId": cid, "state": "PAUSED", "dailyBudget": 99.0}]},
    )
    assert r.status_code == 207
    upd = r.json()["campaigns"]["success"][0]["campaign"]
    assert upd["state"] == "PAUSED"
    assert upd["dailyBudget"] == 99.0

    # 5. Delete
    r = client.delete(f"/sp/campaigns/{cid}", headers=scope_headers)
    assert r.status_code == 200

    r = client.post(
        "/sp/campaigns/list",
        json={"campaignIdFilter": {"include": [cid]}},
        headers=scope_headers,
    )
    assert len(r.json()["campaigns"]) == 0


def test_sp_create_validation_returns_per_item_error(client, scope_headers):
    r = client.post(
        "/sp/campaigns",
        headers=scope_headers,
        json={"campaigns": [{"name": "missing-required"}]},
    )
    assert r.status_code == 207
    body = r.json()["campaigns"]
    assert body["success"] == []
    assert body["error"][0]["code"] == "INVALID_ARGUMENT"


def test_sp_state_filter(client, scope_headers):
    r = client.post(
        "/sp/campaigns/list",
        json={"stateFilter": {"include": ["ENABLED"]}},
        headers=scope_headers,
    )
    assert r.status_code == 200
    assert all(c["state"] == "ENABLED" for c in r.json()["campaigns"])


def test_sp_keyword_create_under_seeded_ad_group(client, scope_headers):
    # Find a manual campaign + ad group from the seed.
    r = client.post(
        "/sp/campaigns/list",
        json={"stateFilter": {"include": ["ENABLED"]}},
        headers=scope_headers,
    )
    manual = next(c for c in r.json()["campaigns"] if c["targetingType"] == "MANUAL")
    r = client.post(
        "/sp/adGroups/list",
        json={"campaignIdFilter": {"include": [manual["campaignId"]]}},
        headers=scope_headers,
    )
    ag = r.json()["adGroups"][0]

    r = client.post(
        "/sp/keywords",
        headers=scope_headers,
        json={
            "keywords": [
                {
                    "campaignId": manual["campaignId"],
                    "adGroupId": ag["adGroupId"],
                    "keywordText": "pytest keyword",
                    "matchType": "EXACT",
                    "bid": 1.23,
                }
            ]
        },
    )
    assert r.status_code == 207
    success = r.json()["keywords"]["success"]
    assert len(success) == 1
    kw = success[0]["keyword"]
    assert kw["keywordText"] == "pytest keyword"
    assert kw["matchType"] == "EXACT"
    assert kw["bid"] == 1.23
