"""
Preguntas e intervenciones. Funciones PURAS, sin LLM.
"""
from __future__ import annotations


def total_questions(segments: list[dict]) -> int:
    """Cuenta signos de cierre '?' en los turnos del docente."""
    return sum(
        s.get("text", "").count("?")
        for s in segments
        if s.get("speaker") == "teacher"
    )


def student_interventions(segments: list[dict]) -> int:
    """Número de turnos de speakers distintos de 'teacher'."""
    return sum(1 for s in segments if s.get("speaker") != "teacher")
