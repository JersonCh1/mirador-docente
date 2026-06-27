"""
EL CONTRATO JSON (CONGELADO) — backend side.

Este módulo es la única fuente de verdad del shape que viaja entre backend y
frontend. Su espejo exacto vive en `frontend/src/types.ts`. Nadie cambia un campo
sin avisar al dueño del contrato.

Todos los `timestamp` / `start` / `end` están en SEGUNDOS (float) desde el inicio
de la grabación. Los `score` están en escala 1–4 (max_score = 4 en el MVP).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, BeforeValidator, Field, field_validator

# Campos string generados por el LLM: tolera null → ""
_Str = Annotated[str, BeforeValidator(lambda v: "" if v is None else v)]

Platform = Literal["meet", "zoom", "teams", "upload"]
Status = Literal[
    "uploaded",
    "transcribing",
    "analyzing",
    "validating",
    "ready",
    "failed",
]
Speaker = Literal["teacher", "student"]


# --------------------------------------------------------------------------- #
# metadata
# --------------------------------------------------------------------------- #
class Metadata(BaseModel):
    course: str
    teacher: str
    date: str  # ISO date (YYYY-MM-DD)
    platform: Platform = "upload"
    duration_seconds: float = 0
    objectives: Optional[list[str]] = None


# --------------------------------------------------------------------------- #
# transcript
# --------------------------------------------------------------------------- #
class Segment(BaseModel):
    speaker: Speaker
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    segments: list[Segment] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# metrics  (deterministas, CERO LLM)
# --------------------------------------------------------------------------- #
class Silence(BaseModel):
    start: float
    end: float


class FillerWord(BaseModel):
    word: str
    n: int


class FillerWords(BaseModel):
    count: int = 0
    top: list[FillerWord] = Field(default_factory=list)


class VisualSegment(BaseModel):
    start: float
    end: float
    type: Literal["slides", "whiteboard", "screen_share", "none"]


class Metrics(BaseModel):
    talk_ratio_teacher: float = 0.0
    talk_ratio_students: float = 0.0
    words_per_minute: float = 0.0
    total_questions: int = 0
    student_interventions: int = 0
    long_silences: list[Silence] = Field(default_factory=list)
    filler_words: FillerWords = Field(default_factory=FillerWords)
    visual_timeline: list[VisualSegment] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# analysis  (juicio cualitativo del LLM, anclado en evidencia)
# --------------------------------------------------------------------------- #
class Evidence(BaseModel):
    timestamp: float
    quote: _Str = ""  # cita TEXTUAL EXACTA de un segmento de la transcripción
    comment: Optional[str] = None


class Dimension(BaseModel):
    dimension_id: str
    name: str
    score: Optional[int] = None  # 1–4, null si no observable
    max_score: int = 4
    observable: bool = True
    summary: _Str = ""
    evidence: list[Evidence] = Field(default_factory=list)

    @field_validator("score", mode="before")
    @classmethod
    def _round_score(cls, v: object) -> object:
        # El LLM a veces devuelve 3.5 en vez de 3 o 4 — redondeamos.
        if isinstance(v, float):
            return round(v)
        return v


class Framework(BaseModel):
    framework_id: str
    framework_name: str
    overall_score: Optional[float] = None  # promedio de dimensiones observables
    dimensions: list[Dimension] = Field(default_factory=list)


class Strength(BaseModel):
    title: _Str = ""
    detail: _Str = ""
    timestamp: Optional[float] = None


class Improvement(BaseModel):
    title: _Str = ""
    detail: _Str = ""
    timestamp: Optional[float] = None
    suggestion: _Str = ""


class Deviation(BaseModel):
    start: float
    end: float
    note: _Str = ""


class ObjectiveAlignment(BaseModel):
    aligned_pct: float
    deviations: list[Deviation] = Field(default_factory=list)


class Analysis(BaseModel):
    frameworks: list[Framework] = Field(default_factory=list)
    strengths: list[Strength] = Field(default_factory=list)
    improvements: list[Improvement] = Field(default_factory=list)
    objective_alignment: Optional[ObjectiveAlignment] = None


# --------------------------------------------------------------------------- #
# student_feedback  (MOCKEADO en el MVP)
# --------------------------------------------------------------------------- #
class StudentRecommendation(BaseModel):
    title: str
    detail: str = ""


class StudentFeedback(BaseModel):
    participation_level: Literal["low", "medium", "high"] = "medium"
    interventions: int = 0
    speaking_seconds: float = 0
    recommendations: list[StudentRecommendation] = Field(default_factory=list)
    review_topics: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Session  (objeto raíz del contrato)
# --------------------------------------------------------------------------- #
class Session(BaseModel):
    session_id: str
    status: Status
    progress: int = 0
    error: Optional[str] = None
    metadata: Metadata
    transcript: Optional[Transcript] = None
    metrics: Optional[Metrics] = None
    analysis: Optional[Analysis] = None
    student_feedback: Optional[StudentFeedback] = None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Vistas ligeras para la lista y el polling
# --------------------------------------------------------------------------- #
class SessionSummary(BaseModel):
    """Fila para la biblioteca / tendencias (GET /api/sessions)."""

    session_id: str
    course: str
    teacher: str
    date: str
    status: Status
    overall_score: Optional[float] = None


class StatusResponse(BaseModel):
    """Respuesta ligera para polling barato (GET /api/sessions/{id}/status)."""

    status: Status
    progress: int
    error: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    status: Status
