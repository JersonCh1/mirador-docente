"""
Construcción del prompt de análisis pedagógico. El LLM actúa como evaluador
experto y DEBE anclar cada juicio en evidencia textual con timestamp.
"""
from __future__ import annotations

import json


def _transcript_lines(transcript: dict) -> str:
    lines = []
    for s in (transcript or {}).get("segments", []):
        lines.append(
            f"[{s.get('start')}–{s.get('end')}] ({s.get('speaker')}): {s.get('text')}"
        )
    return "\n".join(lines)


def build_prompt(
    transcript: dict,
    metrics: dict,
    frameworks: list[dict],
    objectives: list[str] | None,
) -> str:
    frameworks_json = json.dumps(frameworks, ensure_ascii=False, indent=2)
    metrics_json = json.dumps(metrics, ensure_ascii=False, indent=2)
    objectives_json = json.dumps(objectives or [], ensure_ascii=False)
    transcript_block = _transcript_lines(transcript)

    return f"""Eres un evaluador pedagógico experto en formación docente. Analizas la
grabación de UNA clase virtual y produces retroalimentación formativa, con tono
de coaching (acompañamiento, no sanción), SIEMPRE anclada en evidencia.

REGLAS ESTRICTAS (obligatorias):
1. EVIDENCIA OBLIGATORIA. Cada dimensión, fortaleza y mejora DEBE incluir al menos
   una evidencia con `timestamp` (en segundos) y una `quote` que sea una cita
   TEXTUAL EXACTA, copiada carácter por carácter, de un segmento de la
   transcripción. Si no encuentras evidencia textual para un juicio, NO lo emitas.
2. SOLO DIMENSIONES OBSERVABLES. Evalúa únicamente las dimensiones cuyo
   `observable_from_recording` es true. Para las no observables, emítelas con
   `observable: false`, `score: null`, `evidence: []` y un `summary` que explique
   por qué no es evaluable desde una sola grabación.
3. SCORE entero de 1 a 4 (`max_score` = 4). El `overall_score` de cada marco es el
   PROMEDIO de los scores de SUS dimensiones observables, redondeado a 1 decimal.
4. TONO COACHING. Cada mejora (`improvements`) debe traer una `suggestion`
   accionable y concreta. Nada de juicios punitivos.
5. OBJETIVOS. Si hay objetivos declarados, calcula `objective_alignment` con
   `aligned_pct` (0–1) y `deviations` (tramos start/end con nota). Si NO hay
   objetivos, devuelve `objective_alignment: null`.
6. SALIDA. Responde ÚNICAMENTE con JSON válido correspondiente a la sub-estructura
   "analysis" del contrato (abajo). SIN markdown, SIN ```fences```, SIN texto extra.

ESTRUCTURA DE SALIDA (exacta):
{{
  "frameworks": [
    {{
      "framework_id": "...",
      "framework_name": "...",
      "overall_score": <float|null>,
      "dimensions": [
        {{
          "dimension_id": "...",
          "name": "...",
          "score": <int 1-4|null>,
          "max_score": 4,
          "observable": <bool>,
          "summary": "...",
          "evidence": [{{"timestamp": <float>, "quote": "<cita exacta>", "comment": "..."}}]
        }}
      ]
    }}
  ],
  "strengths": [{{"title": "...", "detail": "...", "timestamp": <float>}}],
  "improvements": [{{"title": "...", "detail": "...", "timestamp": <float>, "suggestion": "..."}}],
  "objective_alignment": {{"aligned_pct": <float 0-1>, "deviations": [{{"start": <float>, "end": <float>, "note": "..."}}]}} | null
}}

MARCOS A EVALUAR (evalúa exactamente estas dimensiones y respeta sus ids):
{frameworks_json}

OBJETIVOS DECLARADOS DE LA SESIÓN:
{objectives_json}

MÉTRICAS DETERMINISTAS YA CALCULADAS (úsalas como contexto, no las recalcules):
{metrics_json}

TRANSCRIPCIÓN (formato [start–end] (speaker): texto):
{transcript_block}

Recuerda: SOLO el JSON de "analysis", con citas textuales exactas."""
