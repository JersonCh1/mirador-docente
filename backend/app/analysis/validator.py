"""
Validador anti-alucinación (CÓDIGO puro, sin LLM). Verifica que cada `quote` de
la evidencia exista textualmente en algún segmento de la transcripción y que su
`timestamp` caiga cerca de ese segmento. Las evidencias que no se anclan se
descartan. Devuelve el análisis limpio + un reporte de validación para debug.
"""
from __future__ import annotations

import re
import unicodedata

# Tolerancia (segundos) entre el timestamp de la cita y el rango del segmento.
TIMESTAMP_TOLERANCE = 5.0


def _normalize(text: str) -> str:
    """lower + colapsa espacios + sin tildes, para comparar de forma robusta."""
    t = (text or "").lower().strip()
    t = "".join(
        c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn"
    )
    t = re.sub(r"\s+", " ", t)
    return t


def _build_index(transcript: dict) -> list[tuple[str, float, float]]:
    index = []
    for s in (transcript or {}).get("segments", []):
        index.append(
            (_normalize(s.get("text", "")), float(s.get("start", 0)), float(s.get("end", 0)))
        )
    return index


def _find_segment(quote: str, index: list[tuple[str, float, float]]):
    """Devuelve (start, end) del segmento que contiene la cita, o None."""
    nq = _normalize(quote)
    if not nq:
        return None
    for seg_text, start, end in index:
        if nq in seg_text or seg_text in nq:
            return start, end
    return None


def _timestamp_ok(timestamp, start: float, end: float) -> bool:
    if timestamp is None:
        return True  # sin timestamp no penalizamos (la cita ya ancló)
    try:
        ts = float(timestamp)
    except (TypeError, ValueError):
        return False
    return (start - TIMESTAMP_TOLERANCE) <= ts <= (end + TIMESTAMP_TOLERANCE)


def validate_analysis(analysis: dict, transcript: dict) -> tuple[dict, dict]:
    index = _build_index(transcript)
    report = {"valid": 0, "invalid": 0, "total": 0}

    cleaned = dict(analysis or {})
    frameworks = []
    for fw in (analysis or {}).get("frameworks", []):
        fw_copy = dict(fw)
        dims = []
        for dim in fw.get("dimensions", []):
            dim_copy = dict(dim)
            kept_evidence = []
            for ev in dim.get("evidence", []):
                report["total"] += 1
                seg = _find_segment(ev.get("quote", ""), index)
                if seg is not None and _timestamp_ok(ev.get("timestamp"), seg[0], seg[1]):
                    report["valid"] += 1
                    kept_evidence.append(ev)
                else:
                    report["invalid"] += 1  # alucinación → descartada
            dim_copy["evidence"] = kept_evidence
            dims.append(dim_copy)
        fw_copy["dimensions"] = dims
        frameworks.append(fw_copy)

    cleaned["frameworks"] = frameworks
    return cleaned, report
