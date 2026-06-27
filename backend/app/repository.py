"""
Patrón Repository sobre SQLAlchemy. TODA la lógica de DB pasa por aquí, de modo
que migrar a Postgres (o a otro store) no toca el resto de la app.

Incluye los ensambladores del contrato (to_session_contract / to_summary) que
convierten una fila ORM en el shape congelado de `schemas.py`.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import SessionRow

# Claves de artefacto válidas para save_artifact.
ARTIFACT_KEYS = {
    "transcript_json",
    "metrics_json",
    "analysis_json",
    "student_feedback_json",
}


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- escritura ---------------------------------------------------------
    def create(self, metadata: dict, recording_ref: Optional[str] = None) -> str:
        row = SessionRow(
            status="uploaded",
            progress=0,
            metadata_json=metadata or {},
            recording_ref=recording_ref,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row.id

    def update_status(
        self,
        id: str,
        status: str,
        progress: int,
        error: Optional[str] = None,
    ) -> None:
        row = self.get(id)
        if row is None:
            return
        row.status = status
        row.progress = progress
        if error is not None:
            row.error = error
        elif status in ("ready", "analyzing", "transcribing", "validating"):
            row.error = None
        self.db.add(row)
        self.db.commit()

    def update_recording_ref(self, id: str, ref: str) -> None:
        """Reapunta la grabación de la sesión (p. ej. tras descargar una URL a disco)."""
        row = self.get(id)
        if row is None:
            return
        row.recording_ref = ref
        self.db.add(row)
        self.db.commit()

    def save_artifact(self, id: str, key: str, data) -> None:
        if key not in ARTIFACT_KEYS:
            raise ValueError(
                f"Clave de artefacto inválida: {key!r}. Válidas: {sorted(ARTIFACT_KEYS)}"
            )
        row = self.get(id)
        if row is None:
            raise ValueError(f"Sesión no encontrada: {id}")
        setattr(row, key, data)
        self.db.add(row)
        self.db.commit()

    # --- lectura -----------------------------------------------------------
    def get(self, id: str) -> Optional[SessionRow]:
        return self.db.get(SessionRow, id)

    def list(
        self,
        course: Optional[str] = None,
        teacher: Optional[str] = None,
    ) -> list[SessionRow]:
        stmt = select(SessionRow).order_by(SessionRow.created_at.desc())
        rows = list(self.db.execute(stmt).scalars().all())
        # Filtros aplicados en Python: los campos viven dentro de metadata_json.
        if course:
            rows = [r for r in rows if (r.metadata_json or {}).get("course") == course]
        if teacher:
            rows = [r for r in rows if (r.metadata_json or {}).get("teacher") == teacher]
        return rows

    # --- ensambladores del contrato ---------------------------------------
    def to_session_contract(self, row: SessionRow) -> dict:
        """Construye el objeto `Session` completo del contrato desde la fila."""
        meta = dict(row.metadata_json or {})
        # Asegurar duration_seconds desde el transcript si no estaba seteado.
        transcript = row.transcript_json
        if transcript and not meta.get("duration_seconds"):
            segs = transcript.get("segments") or []
            if segs:
                meta["duration_seconds"] = max(s.get("end", 0) for s in segs)
        meta.setdefault("platform", "upload")
        meta.setdefault("duration_seconds", 0)

        return {
            "session_id": row.id,
            "status": row.status,
            "progress": row.progress,
            "error": row.error,
            "metadata": meta,
            "transcript": transcript,
            "metrics": row.metrics_json,
            "analysis": row.analysis_json,
            "student_feedback": row.student_feedback_json,
            "created_at": row.created_at,
        }

    def to_summary(self, row: SessionRow) -> dict:
        """Fila ligera para la lista (GET /api/sessions)."""
        meta = row.metadata_json or {}
        return {
            "session_id": row.id,
            "course": meta.get("course", ""),
            "teacher": meta.get("teacher", ""),
            "date": meta.get("date", ""),
            "status": row.status,
            "overall_score": self._overall_score(row),
        }

    @staticmethod
    def _overall_score(row: SessionRow) -> Optional[float]:
        """Promedio de overall_score de los frameworks observables, o None."""
        analysis = row.analysis_json
        if not analysis:
            return None
        scores = [
            fw["overall_score"]
            for fw in analysis.get("frameworks", [])
            if fw.get("overall_score") is not None
        ]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 1)
