from __future__ import annotations

import base64
import json
from typing import Any


def encode_next_token(offset: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"o": offset}).encode()).decode()


def decode_next_token(token: str | None) -> int:
    if not token:
        return 0
    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        return int(data.get("o", 0))
    except Exception:
        return 0


def paginate(items: list[Any], next_token: str | None, max_results: int | None) -> tuple[list[Any], str | None]:
    start = decode_next_token(next_token)
    size = max_results or 100
    page = items[start : start + size]
    nxt = encode_next_token(start + size) if start + size < len(items) else None
    return page, nxt


def apply_state_filter(items: list[Any], include: list[str] | None, attr: str = "state") -> list[Any]:
    if not include:
        return items
    s = {x.upper() for x in include}
    return [i for i in items if str(getattr(i, attr, "")).upper() in s]


def apply_id_filter(items: list[Any], include: list[str] | None, attr: str) -> list[Any]:
    if not include:
        return items
    s = {str(x) for x in include}
    return [i for i in items if str(getattr(i, attr, "")) in s]
