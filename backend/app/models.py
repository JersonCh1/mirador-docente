"""
Modelos ORM (SQLAlchemy 2.x). El estado persistido de una sesión vive en una
sola fila `SessionRow`; cada artefacto del pipeline (transcript, metrics,
analysis, student_feedback) se guarda como JSON para no acoplarnos al shape.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    status: Mapped[str] = mapped_column(String, default="uploaded", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(String, nullable=True)

    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    transcript_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    student_feedback_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    recording_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
