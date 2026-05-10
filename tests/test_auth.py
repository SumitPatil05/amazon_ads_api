from __future__ import annotations


def test_token_refresh_flow(client):
    r = client.post(
        "/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": "Atzr|whatever",
            "client_id": "amzn1.application-oa2-client.demo",
            "client_secret": "demo",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["access_token"]
    assert body["refresh_token"].startswith("Atzr|")


def test_token_grant_type_validation(client):
    r = client.post(
        "/auth/o2/token",
        data={
            "grant_type": "weird",
            "client_id": "x",
            "client_secret": "y",
        },
    )
    assert r.status_code == 400


def test_protected_endpoint_requires_bearer(client):
    r = client.get("/v2/profiles")
    assert r.status_code == 401
    assert "details" in r.json()["detail"]


def test_protected_endpoint_requires_client_id(client):
    # Get a valid bearer first.
    r = client.post(
        "/auth/o2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": "Atzr|t",
            "client_id": "x",
            "client_secret": "y",
        },
    )
    token = r.json()["access_token"]
    r = client.get("/v2/profiles", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_profile_scope_required_for_campaigns(client, auth_headers):
    r = client.post("/sp/campaigns/list", json={}, headers=auth_headers)
    assert r.status_code == 401


def test_unknown_profile_scope_rejected(client, auth_headers):
    r = client.post(
        "/sp/campaigns/list",
        json={},
        headers={**auth_headers, "Amazon-Advertising-API-Scope": "999999999"},
    )
    assert r.status_code == 403
