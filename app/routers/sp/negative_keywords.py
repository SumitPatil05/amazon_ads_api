from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import AuthContext, require_profile_scope
from app.models.sp import SPNegativeKeyword
from app.routers.sp._helpers import apply_id_filter, apply_state_filter, paginate
from app.schemas.sp_v3 import NegativeKeywordCreate
from app.services.ids import numeric_id

router = APIRouter(prefix="/sp/negativeKeywords", tags=["sp-negative-keywords"])


def _to_dict(k: SPNegativeKeyword) -> dict[str, Any]:
    return {
        "keywordId": k.keyword_id,
        "campaignId": k.campaign_id,
        "adGroupId": k.ad_group_id,
        "keywordText": k.keyword_text,
        "matchType": k.match_type,
        "state": k.state,
    }


@router.post("/list")
def list_negative_keywords(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    rows = db.query(SPNegativeKeyword).filter(SPNegativeKeyword.profile_id == auth.profile_id).all()
    rows = apply_state_filter(rows, (body.get("stateFilter") or {}).get("include"))
    rows = apply_id_filter(rows, (body.get("campaignIdFilter") or {}).get("include"), attr="campaign_id")
    rows = apply_id_filter(rows, (body.get("adGroupIdFilter") or {}).get("include"), attr="ad_group_id")
    page, nxt = paginate(rows, body.get("nextToken"), body.get("maxResults"))
    return {"negativeKeywords": [_to_dict(r) for r in page], "nextToken": nxt, "totalResults": len(rows)}


@router.post("", status_code=status.HTTP_207_MULTI_STATUS)
def create_negative_keywords(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("negativeKeywords") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        try:
            data = NegativeKeywordCreate.model_validate(item)
        except Exception as exc:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": str(exc)})
            continue
        kid = numeric_id(11)
        nk = SPNegativeKeyword(
            keyword_id=kid,
            campaign_id=data.campaignId,
            ad_group_id=data.adGroupId,
            profile_id=auth.profile_id,
            keyword_text=data.keywordText,
            match_type=data.matchType.upper(),
            state=data.state.upper(),
        )
        db.add(nk)
        success.append({"index": i, "keywordId": kid, "negativeKeyword": _to_dict(nk)})
    db.commit()
    return {"negativeKeywords": {"success": success, "error": error}}


@router.put("", status_code=status.HTTP_207_MULTI_STATUS)
def update_negative_keywords(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    items = body.get("negativeKeywords") or []
    success: list[dict[str, Any]] = []
    error: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        kid = item.get("keywordId")
        if not kid:
            error.append({"index": i, "code": "INVALID_ARGUMENT", "details": "keywordId required"})
            continue
        nk = (
            db.query(SPNegativeKeyword)
            .filter(SPNegativeKeyword.profile_id == auth.profile_id, SPNegativeKeyword.keyword_id == kid)
            .first()
        )
        if nk is None:
            error.append({"index": i, "code": "NOT_FOUND", "details": f"Negative keyword {kid} not found"})
            continue
        if "state" in item:
            nk.state = str(item["state"]).upper()
        nk.last_updated_at = datetime.utcnow()
        success.append({"index": i, "keywordId": nk.keyword_id, "negativeKeyword": _to_dict(nk)})
    db.commit()
    return {"negativeKeywords": {"success": success, "error": error}}


@router.delete("/{keyword_id}")
def delete_negative_keyword(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    keyword_id: str = Path(...),
) -> dict[str, Any]:
    nk = (
        db.query(SPNegativeKeyword)
        .filter(SPNegativeKeyword.profile_id == auth.profile_id, SPNegativeKeyword.keyword_id == keyword_id)
        .first()
    )
    if nk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(nk)
    db.commit()
    return {"keywordId": keyword_id, "code": "SUCCESS"}
