"""
Talk ratio: fracción del tiempo hablado por el docente vs. los estudiantes.
Función PURA, sin LLM.
"""
from __future__ import annotations


def _speaking_time(segments: list[dict]) -> tuple[float, float]:
    teacher = 0.0
    students = 0.0
    for s in segments:
        dur = max(0.0, float(s.get("end", 0)) - float(s.get("start", 0)))
        if s.get("speaker") == "teacher":
            teacher += dur
        else:  # cualquier speaker != teacher cuenta como estudiante
            students += dur
    return teacher, students


def talk_ratio(segments: list[dict]) -> tuple[float, float]:
    """Devuelve (teacher_ratio, students_ratio) normalizados a fracción [0, 1]."""
    teacher, students = _speaking_time(segments)
    total = teacher + students
    if total <= 0:
        return 0.0, 0.0
    return round(teacher / total, 2), round(students / total, 2)
