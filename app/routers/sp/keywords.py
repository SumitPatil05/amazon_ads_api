from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sp import SPAdGroup, SPKeyword
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sp_v3 import KeywordCreate, KeywordUpdate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sp/keywords", tags=["sp-keywords"])


def _ts(dt: datetime | None) -> str | None:
    return (dt.isoformat() + "Z") if dt else None


def _to_dict(k: SPKeyword) -> dict[str, Any]:
    return {
        "keywordId": k.keyword_id,
        "campaignId": k.campaign_id,
        "adGroupId": k.ad_group_id,
        "keywordText": k.keyword_text,
        "matchType": k.match_type,
        "state": k.state,
        "bid": k.bid,
        "nativeLanguageKeyword": k.native_language_keyword,
        "nativeLanguageLocale": k.native_language_locale,
        "extendedData": {
            "creationDateTime": _ts(k.created_at),
            "lastUpdateDateTime": _ts(k.last_updated_at),
            "servingStatus": "TARGETING_CLAUSE_STATUS_LIVE" if k.state == "ENABLED" else "TARGETING_CLAUSE_PAUSED",
        },
    }


@router.post("/list")
def list_keywords(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SPKeyword).filter(SPKeyword.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    rows = apply_id_filter(rows, (body.get("keywordIdFilter") or {}).get("include"), attr="keyword_id")
    mt = (body.get("matchTypeFilter") or {}).get("include")
    if mt:
        s = {x.upper() for x in mt}
        rows = [r for r in rows if r.match_type.upper() in s]
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"keywords": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_keywords(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("keywords") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = KeywordCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        ag = (
            db.query(SPAdGroup)
            .filter(SPAdGroup.profile_id == auth.profile_id, SPAdGroup.ad_group_id == data.adGroupId)
            .first()
        )
        if ag is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Ad group {data.adGroupId} not found"})
            continue
        kid = numeric_id(11)
        now = datetime.utcnow()
        k = SPKeyword(
            keyword_id=kid,
            campaign_id=data.campaignId,
            ad_group_id=data.adGroupId,
            profile_id=auth.profile_id,
            keyword_text=data.keywordText,
            match_type=data.matchType.upper(),
            state=data.state.upper(),
            bid=data.bid,
            native_language_keyword=data.nativeLanguageKeyword,
            native_language_locale=data.nativeLanguageLocale,
            created_at=now,
            last_updated_at=now,
        )
        db.add(k)
        success.append({"index": i, "keywordId": kid, "keyword": _to_dict(k)})
    db.commit()
    return {"keywords": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_keywords(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("keywords") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = KeywordUpdate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        k = (
            db.query(SPKeyword)
            .filter(SPKeyword.profile_id == auth.profile_id, SPKeyword.keyword_id == data.keywordId)
            .first()
        )
        if k is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Keyword {data.keywordId} not found"})
            continue
        if data.state is not None:
            k.state = data.state.upper()
        if data.bid is not None:
            k.bid = data.bid
        k.last_updated_at = datetime.utcnow()
        success.append({"index": i, "keywordId": k.keyword_id, "keyword": _to_dict(k)})
    db.commit()
    return {"keywords": {"success": success, "error": error}}


@router.delete("/{keyword_id}")
def delete_keyword(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    keyword_id: str = Path(...),
) -> dict[str, Any]:
    k = (
        db.query(SPKeyword)
        .filter(SPKeyword.profile_id == auth.profile_id, SPKeyword.keyword_id == keyword_id)
        .first()
    )
    if k is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(k)
    db.commit()
    return {"keywordId": keyword_id, "code": "SUCCESS"}
