from __future__ import annotations


def test_list_profiles_returns_seeded(client, auth_headers):
    r = client.get("/v2/profiles", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 3
    sample = items[0]
    assert {"profileId", "countryCode", "currencyCode", "timezone", "accountInfo"} <= set(sample.keys())
    assert {"id", "name", "type", "marketplaceStringId"} <= set(sample["accountInfo"].keys())


def test_get_profile_by_id(client, auth_headers, profile_id):
    r = client.get(f"/v2/profiles/{profile_id}", headers=auth_headers)
    assert r.status_code == 200
    assert str(r.json()["profileId"]) == profile_id


def test_portfolios_listed_and_extended(client, scope_headers):
    r = client.get("/portfolios", headers=scope_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    r = client.get("/portfolios/extended", headers=scope_headers)
    assert r.status_code == 200
    item = r.json()[0]
    assert "creationDate" in item and "servingStatus" in item
