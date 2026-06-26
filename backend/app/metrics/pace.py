"""
Ritmo del docente: palabras por minuto, silencios largos y muletillas.
Funciones PURAS, sin LLM.
"""
from __future__ import annotations

import re
from collections import Counter


def _teacher_segments(segments: list[dict]) -> list[dict]:
    return [s for s in segments if s.get("speaker") == "teacher"]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or "", flags=re.UNICODE))


def words_per_minute(segments: list[dict]) -> float:
    """Palabras del docente / minutos hablados por el docente."""
    teacher = _teacher_segments(segments)
    words = sum(_word_count(s.get("text", "")) for s in teacher)
    seconds = sum(
        max(0.0, float(s.get("end", 0)) - float(s.get("start", 0))) for s in teacher
    )
    if seconds <= 0:
        return 0.0
    return round(words / (seconds / 60.0), 1)


def long_silences(segments: list[dict], threshold: float = 8.0) -> list[dict]:
    """
    Gaps entre el fin de un segmento y el inicio del siguiente mayores al umbral.
    Devuelve [{"start", "end"}].
    """
    ordered = sorted(segments, key=lambda s: float(s.get("start", 0)))
    silences = []
    for prev, nxt in zip(ordered, ordered[1:]):
        gap_start = float(prev.get("end", 0))
        gap_end = float(nxt.get("start", 0))
        if gap_end - gap_start > threshold:
            silences.append({"start": round(gap_start, 2), "end": round(gap_end, 2)})
    return silences


def filler_words(
    segments: list[dict],
    filler_list: list[str],
    top_n: int = 5,
) -> dict:
    """
    Cuenta ocurrencias (case-insensitive, con límites de palabra) de cada muletilla
    de la lista configurable en los turnos del docente. Devuelve
    {"count": int, "top": [{"word", "n"}, ...]} ordenado desc.
    """
    teacher_text = " ".join(
        s.get("text", "") for s in _teacher_segments(segments)
    ).lower()

    counts: Counter = Counter()
    for filler in filler_list:
        f = filler.lower().strip()
        if not f:
            continue
        # \b no funciona junto a signos como '¿'/'?'; usamos lookarounds laxos.
        pattern = r"(?<!\w)" + re.escape(f) + r"(?!\w)"
        n = len(re.findall(pattern, teacher_text))
        if n > 0:
            counts[filler] = n

    total = sum(counts.values())
    top = [
        {"word": word, "n": n}
        for word, n in counts.most_common(top_n)
    ]
    return {"count": total, "top": top}
