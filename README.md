# Amazon Ads API Mock Server

A FastAPI + SQLite mock of the Amazon Ads API that mirrors the official endpoint paths, headers, request/response shapes, and async report behavior. Build your automation against this today, then swap to production by changing only the base URL and credentials.

## What it covers

- **Auth**: Login with Amazon (LWA) OAuth2 token exchange + refresh
- **Account**: Profiles, Portfolios
- **Sponsored Products v3**: campaigns, adGroups, keywords, productAds, targets, negativeKeywords (+ negative targets)
- **Sponsored Brands v4**: campaigns, adGroups, keywords, targets, creatives
- **Sponsored Display**: campaigns, adGroups, productAds, targets
- **Reports v3**: full async lifecycle (PENDING → PROCESSING → COMPLETED), signed download URLs serving gzipped JSON

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data storage/reports
uvicorn app.main:app --reload --port 8080
```

Then open:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

The DB is auto-created and seeded on first run with 3 profiles, portfolios, and a full set of demo campaigns/ad groups/keywords across SP, SB, and SD.

## Deploy on [Render](https://render.com)

1. Push this repo to GitHub (or GitLab / Bitbucket).
2. In Render: **New → Blueprint**, select the repo, and apply [`render.yaml`](render.yaml). Or **New → Web Service**, connect the repo, and set:
   - **Runtime**: Python 3.11
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add an environment variable **`LWA_JWT_SECRET`** (the blueprint can generate one). Optionally set **`PUBLIC_BASE_URL`** to your public URL if you use a custom domain; otherwise Render’s **`RENDER_EXTERNAL_URL`** is used automatically for report download links.
4. Call the service at `https://<your-service>.onrender.com` — use that host for both the API and `POST /auth/o2/token` while testing against the mock.

**Notes:** SQLite and `storage/reports` live on the instance’s **ephemeral disk** — data resets on redeploy or sleep (fine for a demo mock). The free web tier **spins down** after idle; first request after sleep may take ~30s.

## Auth flow

```bash
# 1. Exchange a (mock) refresh token for an access token (LWA shape)
curl -X POST http://localhost:8080/auth/o2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'grant_type=refresh_token&refresh_token=Atzr|mock-refresh-token&client_id=amzn1.application-oa2-client.demo&client_secret=demo-secret'

# 2. Use the access_token plus the seeded profile id (try /v2/profiles to discover)
curl http://localhost:8080/v2/profiles \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Amazon-Advertising-API-ClientId: amzn1.application-oa2-client.demo"
```

In `STRICT_AUTH=false` mode (default) any non-empty `client_id`/`client_secret`/`refresh_token` triple is accepted, which keeps local development friction-free.

## Sponsored Products v3 example

```bash
# List campaigns for a profile
curl -X POST http://localhost:8080/sp/campaigns/list \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Amazon-Advertising-API-ClientId: amzn1.application-oa2-client.demo" \
  -H "Amazon-Advertising-API-Scope: <PROFILE_ID>" \
  -H "Content-Type: application/vnd.spCampaign.v3+json" \
  -H "Accept: application/vnd.spCampaign.v3+json" \
  -d '{"stateFilter":{"include":["ENABLED"]},"maxResults":10}'
```

## Reports v3 example

```bash
# 1. Request a report
curl -X POST http://localhost:8080/reporting/reports \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Amazon-Advertising-API-ClientId: amzn1.application-oa2-client.demo" \
  -H "Amazon-Advertising-API-Scope: <PROFILE_ID>" \
  -H "Content-Type: application/vnd.createasyncreportrequest.v3+json" \
  -d '{
    "name":"sp-campaigns-30d",
    "startDate":"2026-04-10",
    "endDate":"2026-05-09",
    "configuration":{
      "adProduct":"SPONSORED_PRODUCTS",
      "groupBy":["campaign"],
      "columns":["impressions","clicks","cost","sales1d","purchases1d"],
      "reportTypeId":"spCampaigns",
      "timeUnit":"SUMMARY",
      "format":"GZIP_JSON"
    }
  }'

# 2. Poll until COMPLETED
curl http://localhost:8080/reporting/reports/<REPORT_ID> \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Amazon-Advertising-API-ClientId: amzn1.application-oa2-client.demo" \
  -H "Amazon-Advertising-API-Scope: <PROFILE_ID>"

# 3. Download (URL is in the COMPLETED response)
curl <DOWNLOAD_URL> | gunzip
```

## Path to real API later

Because every router uses the **same paths, headers, media types, enums, and JSON shapes** Amazon uses, your client integration switches over by:

1. Pointing `BASE_URL` at `https://advertising-api.amazon.com` (or your regional host).
2. Pointing the LWA token URL at `https://api.amazon.com/auth/o2/token`.
3. Supplying real `client_id`, `client_secret`, `refresh_token`.

No changes to request bodies, response parsing, or polling loops should be required.

## Tests

```bash
pytest -q
```

## Project layout

```
app/
  main.py            FastAPI app, router includes, startup seed
  config.py          Settings (pydantic-settings)
  db.py              SQLAlchemy engine + Session
  deps.py            Auth header dependency
  seed.py            Idempotent demo seed
  auth/              LWA mock + JWT access tokens
  models/            SQLAlchemy ORM models
  schemas/           Pydantic schemas (per API version)
  routers/           profiles, portfolios, sp/, sb/, sd/, reports/
  services/          report_generator, ids
storage/reports/     Generated .json.gz files
tests/               pytest + httpx smoke tests
```
