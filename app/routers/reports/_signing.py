from __future__ import annotations

import base64
import hashlib
import hmac
import time

from app.config import get_settings


def make_download_token(report_id: str, expires_at_epoch: int) -> str:
    secret = get_settings().LWA_JWT_SECRET.encode()
    msg = f"{report_id}|{expires_at_epoch}".encode()
    sig = hmac.new(secret, msg, hashlib.sha256).digest()
    raw = f"{report_id}|{expires_at_epoch}|".encode() + base64.urlsafe_b64encode(sig)
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def verify_download_token(token: str) -> tuple[str, int]:
    pad = "=" * (-len(token) % 4)
    raw = base64.urlsafe_b64decode(token + pad).decode("utf-8", errors="replace")
    try:
        report_id, exp_str, sig_b64 = raw.split("|", 2)
        exp = int(exp_str)
    except Exception as exc:
        raise ValueError("malformed token") from exc
    expected = make_download_token(report_id, exp)
    if not hmac.compare_digest(expected, token):
        raise ValueError("bad signature")
    if time.time() > exp:
        raise ValueError("token expired")
    return report_id, exp
