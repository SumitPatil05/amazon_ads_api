from __future__ import annotations

import itertools
import secrets
import threading
import time

_counter = itertools.count(1)
_counter_lock = threading.Lock()


def numeric_id(digits: int = 12) -> str:
    """Mint a numeric string id resembling Amazon's entity ids.

    Amazon's campaign / ad group / keyword ids are large positive integers
    rendered as strings (typically 10-13 digits). We synthesise something in
    the same shape using a process-monotonic counter combined with time and
    random bits so collisions never happen even in tight loops.
    """
    if digits < 6:
        raise ValueError("digits must be >= 6")
    with _counter_lock:
        n = next(_counter)
    millis = int(time.time() * 1000) & 0xFFFFFFFF
    rnd = secrets.randbelow(10_000)
    base = (millis * 100_000 + (n % 100_000)) * 10_000 + rnd
    s = str(base)
    if len(s) >= digits:
        return s[-digits:]
    return s.rjust(digits, "0")


def request_id() -> str:
    return secrets.token_hex(8).upper()


def report_id() -> str:
    # Amazon report ids look like "amzn1.clicksAPI.<uuid>"; mimic loosely.
    return f"amzn1.clicksAPI.v3.p{numeric_id(8)}.{secrets.token_hex(8)}"
