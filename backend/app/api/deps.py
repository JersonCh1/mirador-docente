"""
Dependencias FastAPI: sesión de DB → Repository, y settings.
"""
from __future__ import annotations

from typing import Iterator

from fastapi import Depends

from ..config import Settings, get_settings as _get_settings
from ..db import SessionLocal
from ..repository import SessionRepository


def get_db() -> Iterator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_repo(db=Depends(get_db)) -> SessionRepository:
    return SessionRepository(db)


def get_settings() -> Settings:
    return _get_settings()
