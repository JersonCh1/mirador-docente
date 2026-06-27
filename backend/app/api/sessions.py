"""
Router de sesiones. Endpoints del contrato bajo /api.

POST /api/sessions acepta DOS modos:
  - multipart/form-data con un archivo (campo `file`) + campos de metadata.
  - application/json con {url, course, teacher, date, platform, objectives}.
"""
from __future__ import annotations

import json
import os
import shutil
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import FileResponse

from ..config import Settings
from ..db import SessionLocal
from ..media.download import UPLOADS_DIR
from ..pipeline.runner import run_pipeline, run_analysis_only
from ..repository import SessionRepository
from ..schemas import (
    CreateSessionResponse,
    Session,
    SessionSummary,
    StatusResponse,
)
from .deps import get_repo, get_settings
from ..chat.agent import chat as agent_chat

router = APIRouter()


def _run_pipeline_bg(session_id: str, recording_ref: str | None, settings: Settings) -> None:
    """Wrapper para BackgroundTasks: usa una sesión de DB propia y aislada."""
    db = SessionLocal()
    try:
        repo = SessionRepository(db)
        run_pipeline(session_id, recording_ref, repo, settings)
    finally:
        db.close()


def _build_metadata(
    course: str,
    teacher: str,
    date: str,
    platform: str,
    objectives,
) -> dict:
    meta = {
        "course": course or "",
        "teacher": teacher or "",
        "date": date or "",
        "platform": platform or "upload",
        "duration_seconds": 0,
    }
    if objectives:
        meta["objectives"] = objectives
    return meta


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: Request,
    background: BackgroundTasks,
    repo: SessionRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
) -> CreateSessionResponse:
    content_type = request.headers.get("content-type", "")
    recording_ref: str | None = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        course = str(form.get("course", ""))
        teacher = str(form.get("teacher", ""))
        date = str(form.get("date", ""))
        platform = str(form.get("platform", "upload"))
        objectives_raw = form.get("objectives")
        objectives = _parse_objectives(objectives_raw)

        upload = form.get("file")
        url_field = str(form.get("url", "")).strip()
        if upload is not None and hasattr(upload, "filename") and upload.filename:
            ext = os.path.splitext(upload.filename)[1]
            stored = os.path.join(UPLOADS_DIR, f"{uuid.uuid4()}{ext}")
            with open(stored, "wb") as out:
                shutil.copyfileobj(upload.file, out)
            recording_ref = stored
        elif url_field:
            # Sin archivo: se pegó una URL de grabación (Drive/Meet/directa).
            recording_ref = url_field
    else:
        # JSON con url + metadata.
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Body JSON inválido.")
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Body JSON debe ser un objeto.")
        course = body.get("course", "")
        teacher = body.get("teacher", "")
        date = body.get("date", "")
        platform = body.get("platform", "upload")
        objectives = body.get("objectives")
        url = body.get("url")
        recording_ref = url  # referencia remota; el FakeProvider la ignora

    metadata = _build_metadata(course, teacher, date, platform, objectives)
    session_id = repo.create(metadata, recording_ref)

    background.add_task(_run_pipeline_bg, session_id, recording_ref, settings)
    return CreateSessionResponse(session_id=session_id, status="uploaded")


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(
    course: str | None = None,
    teacher: str | None = None,
    repo: SessionRepository = Depends(get_repo),
) -> list[SessionSummary]:
    rows = repo.list(course=course, teacher=teacher)
    return [SessionSummary(**repo.to_summary(r)) for r in rows]


@router.get("/sessions/{session_id}", response_model=Session)
def get_session(
    session_id: str,
    repo: SessionRepository = Depends(get_repo),
) -> Session:
    row = repo.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    return Session(**repo.to_session_contract(row))


@router.get("/sessions/{session_id}/status", response_model=StatusResponse)
def get_status(
    session_id: str,
    repo: SessionRepository = Depends(get_repo),
) -> StatusResponse:
    row = repo.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    return StatusResponse(status=row.status, progress=row.progress, error=row.error)


@router.get("/sessions/{session_id}/recording")
def get_recording(
    session_id: str,
    repo: SessionRepository = Depends(get_repo),
) -> FileResponse:
    row = repo.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    ref = row.recording_ref
    if not ref or not os.path.exists(ref):
        raise HTTPException(status_code=404, detail="Grabación no disponible.")
    return FileResponse(ref)


@router.post("/sessions/{session_id}/retry-analysis")
async def retry_analysis(
    session_id: str,
    background: BackgroundTasks,
    repo: SessionRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
) -> StatusResponse:
    """Re-ejecuta analyze→validate→persist sobre el transcript ya guardado.
    Útil cuando el paso de análisis falla sin tener que re-transcribir."""
    row = repo.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if not row.transcript_json:
        raise HTTPException(status_code=400, detail="No hay transcript guardado para esta sesión.")

    def _bg():
        db = SessionLocal()
        try:
            r = SessionRepository(db)
            run_analysis_only(session_id, r, settings)
        finally:
            db.close()

    background.add_task(_bg)
    return StatusResponse(status="analyzing", progress=55, error=None)


@router.post("/sessions/{session_id}/chat")
def chat_session(
    session_id: str,
    payload: dict,
    repo: SessionRepository = Depends(get_repo),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Agente conversacional sobre una sesión específica usando Groq tool use."""
    row = repo.get(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if row.status != "ready":
        raise HTTPException(status_code=400, detail="La sesión aún no tiene análisis completo.")

    user_message = payload.get("message", "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="El campo 'message' es obligatorio.")

    history = payload.get("history", [])

    session_data = repo.to_session_contract(row)

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY no configurada.")

    try:
        reply = agent_chat(session_data, user_message, history, settings.GROQ_API_KEY, settings.GEMINI_API_KEY)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"reply": reply}


def _parse_objectives(raw):
    """Acepta objectives como lista JSON, csv o None (desde un form)."""
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw
    s = str(raw).strip()
    if not s:
        return None
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    return [o.strip() for o in s.split(",") if o.strip()]
