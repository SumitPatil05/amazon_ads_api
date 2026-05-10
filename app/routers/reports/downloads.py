from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.db import SessionLocal
from app.models.reports import Report
from app.routers.reports._signing import verify_download_token

router = APIRouter(tags=["reports-v3"])


@router.get("/downloads/{token}")
def download_report(token: str) -> FileResponse:
    try:
        report_id, _ = verify_download_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "403", "details": f"Invalid or expired download token: {exc}"},
        ) from exc

    with SessionLocal() as db:
        r = db.query(Report).filter(Report.report_id == report_id).first()
        if r is None or r.file_path is None or not os.path.exists(r.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "404", "details": "Report file not found"},
            )
        path = r.file_path
        size = r.file_size or os.path.getsize(path)

    # Serve the gzipped file as raw bytes the way Amazon's signed S3 URLs do:
    # the body is the gzip payload itself, NOT transport-encoded with
    # Content-Encoding: gzip (otherwise HTTP clients would auto-decompress
    # and the consumer wouldn't see the real on-the-wire format).
    return FileResponse(
        path=path,
        media_type="application/octet-stream",
        filename=os.path.basename(path),
        headers={"Content-Length": str(size)},
    )
