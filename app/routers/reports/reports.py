from __future__ import annotations

import random
import threading
import time
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal, get_db
from app.deps import AuthContext, require_profile_scope
from app.models.reports import Report
from app.routers.reports._signing import make_download_token
from app.schemas.reports_v3 import CreateAsyncReportRequest
from app.services.ids import report_id as new_report_id
from app.services.report_generator import generate_report_payload, write_gzip_payload

router = APIRouter(prefix="/reporting/reports", tags=["reports-v3"])


def _ts(dt: datetime | None) -> str | None:
    return (dt.isoformat() + "Z") if dt else None


def _to_dict(r: Report) -> dict[str, Any]:
    out: dict[str, Any] = {
        "reportId": r.report_id,
        "name": r.name,
        "status": r.status,
        "statusDetails": r.status_details,
        "failureReason": r.failure_reason,
        "startDate": r.start_date,
        "endDate": r.end_date,
        "configuration": r.configuration,
        "format": (r.configuration or {}).get("format", "GZIP_JSON"),
        "createdAt": _ts(r.created_at),
        "updatedAt": _ts(r.updated_at),
    }
    if r.status == "COMPLETED" and r.download_token and r.url_expires_at:
        out["url"] = f"{get_settings().PUBLIC_BASE_URL}/downloads/{r.download_token}"
        out["urlExpiresAt"] = _ts(r.url_expires_at)
        out["fileSize"] = r.file_size
    return out


def _process_report(report_id_value: str) -> None:
    """Background worker that flips a report PENDING -> PROCESSING -> COMPLETED."""

    settings = get_settings()
    delay = random.uniform(settings.REPORT_MIN_DELAY_SEC, settings.REPORT_MAX_DELAY_SEC)
    time.sleep(min(delay, 1.0))

    with SessionLocal() as db:
        r = db.query(Report).filter(Report.report_id == report_id_value).first()
        if r is None:
            return
        r.status = "PROCESSING"
        r.status_details = "Generating report data"
        r.updated_at = datetime.utcnow()
        db.commit()

    time.sleep(max(delay - 1.0, 0.5))

    with SessionLocal() as db:
        r = db.query(Report).filter(Report.report_id == report_id_value).first()
        if r is None:
            return
        try:
            rows = generate_report_payload(
                db,
                profile_id=r.profile_id,
                report_id=r.report_id,
                start_date=r.start_date,
                end_date=r.end_date,
                configuration=r.configuration or {},
            )
            file_path, file_size = write_gzip_payload(r.report_id, rows)
            expires_epoch = int(time.time()) + settings.DOWNLOAD_URL_TTL_SEC
            expires_at = datetime.utcfromtimestamp(expires_epoch)
            token = make_download_token(r.report_id, expires_epoch)

            r.status = "COMPLETED"
            r.status_details = f"{len(rows)} rows generated"
            r.file_path = file_path
            r.file_size = file_size
            r.download_token = token
            r.url_expires_at = expires_at
            r.updated_at = datetime.utcnow()
            db.commit()
        except Exception as exc:  # pragma: no cover - defensive
            r.status = "FAILED"
            r.failure_reason = str(exc)
            r.updated_at = datetime.utcnow()
            db.commit()


@router.post("", status_code=status.HTTP_200_OK)
def create_report(
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
    body: CreateAsyncReportRequest = Body(...),
) -> dict[str, Any]:
    rid = new_report_id()
    now = datetime.utcnow()
    r = Report(
        report_id=rid,
        profile_id=auth.profile_id,
        name=body.name,
        status="PENDING",
        status_details="Report queued",
        start_date=body.startDate,
        end_date=body.endDate,
        configuration=body.configuration.model_dump(),
        created_at=now,
        updated_at=now,
    )
    db.add(r)
    db.commit()

    # Run generation off the request thread.
    threading.Thread(target=_process_report, args=(rid,), daemon=True).start()

    return _to_dict(r)


@router.get("/{report_id}")
def get_report(
    report_id: str,
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    r = (
        db.query(Report)
        .filter(Report.profile_id == auth.profile_id, Report.report_id == report_id)
        .first()
    )
    if r is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "404", "details": f"Report {report_id} not found"},
        )
    return _to_dict(r)


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    auth: Annotated[AuthContext, Depends(require_profile_scope)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    r = (
        db.query(Report)
        .filter(Report.profile_id == auth.profile_id, Report.report_id == report_id)
        .first()
    )
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "404"})
    db.delete(r)
    db.commit()
    return {"reportId": report_id, "code": "SUCCESS"}
