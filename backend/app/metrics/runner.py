"""
Runner de métricas: ensambla el objeto `metrics` completo del contrato a partir
del transcript. TODO es determinista (CERO LLM).
"""
from __future__ import annotations

from ..config import Settings, get_settings
from . import pace, questions, talk_ratio


def compute_all_metrics(transcript: dict, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    segments = (transcript or {}).get("segments", []) or []

    teacher_ratio, students_ratio = talk_ratio.talk_ratio(segments)

    return {
        "talk_ratio_teacher": teacher_ratio,
        "talk_ratio_students": students_ratio,
        "words_per_minute": pace.words_per_minute(segments),
        "total_questions": questions.total_questions(segments),
        "student_interventions": questions.student_interventions(segments),
        "long_silences": pace.long_silences(segments, settings.SILENCE_THRESHOLD),
        "filler_words": pace.filler_words(segments, settings.FILLER_WORDS),
        "visual_timeline": [],  # sin análisis de video en el MVP
    }
