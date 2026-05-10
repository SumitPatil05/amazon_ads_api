from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        parent = Path(path).resolve().parent
        parent.mkdir(parents=True, exist_ok=True)


_settings = get_settings()
_ensure_sqlite_dir(_settings.DATABASE_URL)

engine = create_engine(
    _settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if _settings.DATABASE_URL.startswith("sqlite") else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they are registered on the metadata.
    from app.models import (  # noqa: F401
        portfolio,
        profile,
        reports,
        sb,
        sd,
        sp,
    )

    os.makedirs(_settings.REPORTS_STORAGE_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
