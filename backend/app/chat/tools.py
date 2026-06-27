"""
Herramientas (tools) que el agente de chat puede invocar sobre una sesión.
Cada función recibe los datos de la sesión y devuelve texto estructurado.
"""
from __future__ import annotations

import re


def get_analysis(session: dict, framework_id: str | None = None, dimension_id: str | None = None) -> str:
    """Devuelve scores y evidencia del análisis pedagógico."""
    analysis = session.get("analysis") or {}
    frameworks = analysis.get("frameworks", [])
    if not frameworks:
        return "No hay análisis disponible para esta sesión."

    lines = []
    for fw in frameworks:
        if framework_id and fw["framework_id"] != framework_id:
            continue
        lines.append(f"\n=== {fw['framework_name']} (overall: {fw.get('overall_score')}/4) ===")
        for dim in fw.get("dimensions", []):
            if dimension_id and dim["dimension_id"] != dimension_id:
                continue
            score = dim.get("score")
            obs = dim.get("observable", True)
            lines.append(f"\n[{dim['name']}] score={score}/4 observable={obs}")
            lines.append(f"  Resumen: {dim.get('summary','')}")
            for ev in dim.get("evidence", []):
                ts = ev.get("timestamp", 0)
                mins = int(ts) // 60
                secs = int(ts) % 60
                lines.append(f"  [{mins}:{secs:02d}] \"{ev.get('quote','')}\"")
                lines.append(f"         → {ev.get('comment','')}")

    strengths = analysis.get("strengths", [])
    improvements = analysis.get("improvements", [])
    if strengths:
        lines.append("\n=== FORTALEZAS ===")
        for s in strengths:
            ts = s.get("timestamp") or 0
            mins = int(ts) // 60
            lines.append(f"  [{mins}min] {s['title']}: {s.get('detail','')}")
    if improvements:
        lines.append("\n=== MEJORAS ===")
        for i in improvements:
            ts = i.get("timestamp") or 0
            mins = int(ts) // 60
            lines.append(f"  [{mins}min] {i['title']}: {i.get('detail','')} → {i.get('suggestion','')}")

    return "\n".join(lines) if lines else "Sin datos de análisis."


def search_transcript(session: dict, query: str, max_results: int = 5) -> str:
    """Busca fragmentos del transcript que contengan la query (case-insensitive)."""
    transcript = session.get("transcript") or {}
    segments = transcript.get("segments", [])
    if not segments:
        return "No hay transcript disponible."

    query_lower = query.lower()
    matches = []
    for seg in segments:
        text = seg.get("text", "")
        if query_lower in text.lower():
            ts = seg.get("start", 0)
            mins = int(ts) // 60
            secs = int(ts) % 60
            speaker = seg.get("speaker", "?")
            # Muestra hasta 200 chars del fragmento con la query resaltada
            snippet = text[:300] + ("…" if len(text) > 300 else "")
            matches.append(f"[{mins}:{secs:02d}] ({speaker}): {snippet}")
            if len(matches) >= max_results:
                break

    if not matches:
        return f"No se encontraron menciones de '{query}' en el transcript."
    return f"Fragmentos con '{query}':\n" + "\n\n".join(matches)


def get_metrics(session: dict) -> str:
    """Devuelve las métricas calculadas de la sesión (tiempos, silencios, etc.)."""
    metrics = session.get("metrics") or {}
    if not metrics:
        return "No hay métricas disponibles."

    lines = []
    dur = metrics.get("duration_seconds", 0)
    lines.append(f"Duración: {int(dur)//60} min {int(dur)%60} seg")

    speaking = metrics.get("speaking_time", {})
    if speaking:
        for speaker, secs in speaking.items():
            pct = (secs / dur * 100) if dur else 0
            lines.append(f"Tiempo de habla {speaker}: {int(secs)//60}min ({pct:.0f}%)")

    silences = metrics.get("silence_count", 0)
    silence_total = metrics.get("silence_total_seconds", 0)
    if silences:
        lines.append(f"Silencios detectados: {silences} ({int(silence_total)}s total)")

    questions = metrics.get("question_count", 0)
    if questions:
        lines.append(f"Preguntas formuladas: {questions}")

    return "\n".join(lines) if lines else str(metrics)


# Definición de tools en formato Groq/OpenAI function calling
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_analysis",
            "description": (
                "Obtiene los scores, evidencia y feedback pedagógico del análisis de esta clase. "
                "Úsala cuando el docente pregunte por dimensiones, scores, fortalezas o mejoras."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "framework_id": {
                        "type": "string",
                        "description": "Filtrar por framework: 'minedu_mbdd' o 'oecd_talis'. Omitir para ver todos.",
                    },
                    "dimension_id": {
                        "type": "string",
                        "description": "ID de la dimensión específica a consultar (ej: 'cognitive_activation').",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_transcript",
            "description": (
                "Busca fragmentos exactos del transcript de la clase donde se menciona algo. "
                "Úsala cuando el docente pregunte qué dijo, qué pasó en un momento, o quiera citas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto a buscar en el transcript de la clase.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Máximo de fragmentos a devolver (default 5).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_metrics",
            "description": (
                "Obtiene métricas cuantitativas de la clase: tiempo de habla, silencios, preguntas. "
                "Úsala cuando el docente pregunte por estadísticas o datos numéricos de su clase."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]
