"""
Pipeline de procesamiento de una sesión. Cada etapa actualiza status/progress y
guarda su artefacto (para poder re-ejecutar). NUNCA crashea el server: cualquier
excepción marca la sesión como `failed` con el error.

Etapas: ingest → transcribe → metrics → analyze → validate → persist.
"""
from __future__ import annotations

import os
import tempfile

from ..analysis.analyzer import Analyzer
from ..analysis.validator import validate_analysis
from ..config import Settings, get_settings
from ..media.audio import extract_audio
from ..media.download import download_recording, is_remote_url
from ..metrics.runner import compute_all_metrics
from ..providers.factory import get_llm_provider, get_transcription_provider
from ..repository import SessionRepository
from ..rubrics import get_active_frameworks

# student_feedback MOCKEADO en el MVP (copia del bloque del mock canónico).
_STUDENT_FEEDBACK_MOCK = {
    "participation_level": "medium",
    "interventions": 4,
    "speaking_seconds": 24,
    "recommendations": [
        {"title": "Anímate a intervenir en la segunda mitad", "detail": "Tus preguntas en la primera parte fueron muy buenas; mantén ese ritmo durante toda la clase."},
        {"title": "Formula tus dudas con un ejemplo", "detail": "Pedir un ejemplo concreto, como hiciste con seno de equis al cuadrado, ayuda a todo el grupo a entender."},
    ],
    "review_topics": ["Definición formal de derivada", "Regla de la cadena con funciones trigonométricas"],
}


def _build_analysis(transcript, metrics, frameworks, objectives, analyzer) -> dict:
    """
    Llama al Analyzer una vez POR MARCO activo (desacople: cada marco se evalúa
    de forma independiente y swappable) y ensambla el `analysis` del contrato.

    De cada llamada se toma el framework con el id pedido; las secciones globales
    (strengths/improvements/objective_alignment) se toman de la primera llamada.
    """
    out_frameworks = []
    strengths = []
    improvements = []
    objective_alignment = None

    for i, fw in enumerate(frameworks):
        result = analyzer.analyze(transcript, metrics, [fw], objectives)

        # Selecciona el framework con el id pedido (el fake devuelve todos).
        wanted = fw["framework_id"]
        matched = [
            f for f in result.get("frameworks", [])
            if f.get("framework_id") == wanted
        ]
        out_frameworks.extend(matched or result.get("frameworks", []))

        if i == 0:
            strengths = result.get("strengths", []) or []
            improvements = result.get("improvements", []) or []
            objective_alignment = result.get("objective_alignment")

    return {
        "frameworks": out_frameworks,
        "strengths": strengths,
        "improvements": improvements,
        "objective_alignment": objective_alignment,
    }


def run_pipeline(
    session_id: str,
    recording_ref: str | None,
    repo: SessionRepository,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    try:
        # 1) INGEST -------------------------------------------------------
        repo.update_status(session_id, "transcribing", 5)
        local_ref = recording_ref

        # Si es una URL remota (Drive/Meet/directa) y hay un transcriptor REAL,
        # la descargamos a disco para procesar la grabación de verdad. En modo
        # fake no se descarga: el FakeProvider ignora el audio (demo sin keys).
        if is_remote_url(recording_ref) and settings.TRANSCRIPTION_PROVIDER.lower() != "fake":
            local_ref = download_recording(recording_ref)
            repo.update_recording_ref(session_id, local_ref)
            repo.update_status(session_id, "transcribing", 10)

        audio_path = local_ref
        if local_ref and os.path.exists(local_ref):
            out = os.path.join(
                tempfile.gettempdir(), f"mirador_{session_id}.wav"
            )
            # La extracción de audio es una OPTIMIZACIÓN, no un requisito duro:
            # si ffmpeg falla (archivo no-video, corrupto, etc.) seguimos con la
            # ref original. El FakeProvider la ignora; AssemblyAI acepta video.
            try:
                audio_path = extract_audio(local_ref, out)
            except Exception:
                audio_path = local_ref

        # 2) TRANSCRIBE ---------------------------------------------------
        transcriber = get_transcription_provider(settings)
        transcript = transcriber.transcribe(audio_path or "")
        repo.save_artifact(session_id, "transcript_json", transcript)
        repo.update_status(session_id, "transcribing", 40)

        # 3) METRICS ------------------------------------------------------
        metrics = compute_all_metrics(transcript, settings)
        repo.save_artifact(session_id, "metrics_json", metrics)
        repo.update_status(session_id, "analyzing", 55)

        # 4) ANALYZE ------------------------------------------------------
        row = repo.get(session_id)
        objectives = (row.metadata_json or {}).get("objectives") if row else None
        frameworks = get_active_frameworks(settings)
        analyzer = Analyzer(get_llm_provider(settings))
        analysis = _build_analysis(
            transcript, metrics, frameworks, objectives, analyzer
        )
        repo.update_status(session_id, "validating", 90)

        # 5) VALIDATE -----------------------------------------------------
        cleaned, _report = validate_analysis(analysis, transcript)
        repo.save_artifact(session_id, "analysis_json", cleaned)
        repo.update_status(session_id, "validating", 95)

        # 6) PERSIST ------------------------------------------------------
        repo.save_artifact(session_id, "student_feedback_json", _STUDENT_FEEDBACK_MOCK)
        repo.update_status(session_id, "ready", 100)

    except Exception as e:  # noqa: BLE001 - nunca crashear el server
        repo.update_status(session_id, "failed", 100, error=str(e))
