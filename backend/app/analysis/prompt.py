"""
Construcción del prompt de análisis pedagógico. El LLM actúa como evaluador
experto y DEBE anclar cada juicio en evidencia textual con timestamp.
"""
from __future__ import annotations

import json

# Groq free tier: 12k TPM. Input ~6k + output 4k = 10k total.
# Framework JSON + sistema ≈ 3k tokens (12k chars). Transcript: hasta 6k chars.
_MAX_TRANSCRIPT_CHARS = 14_000   # límite total del bloque de transcript
_WINDOW_SECS = 180               # ventana de tiempo: cada 3 minutos, 1 muestra
_CHARS_PER_WINDOW = 400          # chars que se muestran por ventana


def _split_into_windows(segments: list[dict]) -> list[dict]:
    """
    Convierte segmentos (posiblemente muy largos) en ventanas de 3 min.

    Problema que resuelve: AssemblyAI a veces devuelve UN segmento de 30 min
    para un monólogo largo. Con truncación por chars solo se ve el inicio.
    Aquí partimos el texto del segmento en ventanas proporcionales al tiempo,
    asignando a cada ventana un timestamp real y los chars correspondientes.
    """
    windows = []
    for seg in segments:
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "")
        speaker = seg.get("speaker", "teacher")
        duration = end - start

        if duration <= _WINDOW_SECS or not text:
            # Segmento corto: lo muestra completo (truncado a max chars).
            windows.append({
                "start": start, "end": end,
                "speaker": speaker,
                "text": text[:_CHARS_PER_WINDOW] + ("…" if len(text) > _CHARS_PER_WINDOW else "")
            })
        else:
            # Segmento largo: lo parte en ventanas proporcionales.
            n_windows = max(2, int(duration / _WINDOW_SECS))
            chars_per_win = max(1, len(text) // n_windows)
            for i in range(n_windows):
                win_start = start + i * (duration / n_windows)
                win_end = start + (i + 1) * (duration / n_windows)
                chunk = text[i * chars_per_win: (i + 1) * chars_per_win]
                chunk = chunk[:_CHARS_PER_WINDOW] + ("…" if len(chunk) > _CHARS_PER_WINDOW else "")
                windows.append({
                    "start": win_start, "end": win_end,
                    "speaker": speaker, "text": chunk
                })
    return windows


def _transcript_lines(transcript: dict) -> str:
    """
    Serializa el transcript con cobertura proporcional de TODA la clase.
    Segmentos largos se parten en ventanas de 3 min para que los últimos
    30 min de clase no queden invisibles para el LLM.
    """
    segments = (transcript or {}).get("segments", [])
    if not segments:
        return ""

    total_dur = segments[-1].get("end", 0)
    windows = _split_into_windows(segments)

    # Si hay demasiadas ventanas, muestrea uniformemente.
    max_windows = _MAX_TRANSCRIPT_CHARS // (_CHARS_PER_WINDOW + 60)
    if len(windows) > max_windows:
        step = len(windows) // max_windows
        windows = windows[::step]

    lines = [
        f"[{w['start']:.0f}s/{w['start']/60:.1f}min] ({w['speaker']}): {w['text']}"
        for w in windows
    ]
    result = "\n".join(lines)

    if len(result) > _MAX_TRANSCRIPT_CHARS:
        result = result[:_MAX_TRANSCRIPT_CHARS] + "\n[…recortado]"

    header = (
        f"[Clase de {total_dur/60:.1f} min · {len(segments)} segmentos AssemblyAI "
        f"→ {len(windows)} ventanas de ~{_WINDOW_SECS//60} min · "
        f"texto truncado a {_CHARS_PER_WINDOW} chars/ventana para cobertura total]\n"
    )
    return header + result


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
grabación de UNA clase y produces retroalimentación formativa con tono de
coaching (acompañamiento, no sanción), SIEMPRE anclada en evidencia concreta.

REGLAS ESTRICTAS — incumplirlas invalida el resultado:

1. CITA TEXTUAL Y SEMÁNTICAMENTE RELEVANTE.
   La `quote` de cada evidencia debe:
   a) Ser copiada CARÁCTER POR CARÁCTER del texto de la transcripción (sin parafrasear).
   b) Ser DIRECTAMENTE RELEVANTE a la dimensión que evidencia. NO uses una cita
      de saludos o logística para evidenciar activación cognitiva. Si no hay cita
      relevante, pon `evidence: []` y baja el score — no inventes conexiones.

2. COBERTURA DE TODA LA CLASE.
   El transcript abarca {(transcript or {}).get('segments', [{}])[-1].get('end', 0)/60:.0f} minutos.
   Busca evidencia en distintos momentos (inicio, desarrollo, cierre).
   No concentres todas las citas en los primeros minutos.

3. SOLO DIMENSIONES OBSERVABLES.
   Dimensiones con `observable_from_recording: false` → emítelas con
   `observable: false`, `score: null`, `evidence: []`.

4. SCORES DIFERENCIALES.
   No pongas el mismo score a todas las dimensiones. Cada una merece una
   valoración honesta: un 4 es excepcional, un 2 es claramente mejorable.
   El `overall_score` es el promedio de las dimensiones observables.

5. FORTALEZAS Y MEJORAS CON SUGERENCIAS.
   Mínimo 3 fortalezas y 3 mejoras, cada una con detalle específico de ESTA clase
   (no genérico). Cada mejora lleva una `suggestion` concreta y accionable.

6. TONO. Coaching, nunca punitivo. Lenguaje en segunda persona ("el docente..." o
   "se observa que...").

7. SALIDA. ÚNICAMENTE JSON válido. SIN markdown, SIN ```fences```, SIN texto extra.

ESTRUCTURA DE SALIDA:
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
          "summary": "<descripción específica de lo observado en ESTA clase, 2-3 oraciones>",
          "evidence": [{{"timestamp": <float segundos>, "quote": "<cita exacta del transcript>", "comment": "<por qué esta cita evidencia la dimensión>"}}]
        }}
      ]
    }}
  ],
  "strengths": [{{"title": "...", "detail": "<específico de esta clase>", "timestamp": <float>}}],
  "improvements": [{{"title": "...", "detail": "...", "timestamp": <float>, "suggestion": "<acción concreta>'"}}],
  "objective_alignment": {{"aligned_pct": <0-1>, "deviations": [{{"start": <float>, "end": <float>, "note": "..."}}]}} | null
}}

MARCOS A EVALUAR:
{frameworks_json}

OBJETIVOS DE LA SESIÓN:
{objectives_json}

MÉTRICAS (ya calculadas — úsalas como contexto):
{metrics_json}

TRANSCRIPCIÓN (formato [inicio–fin / min] (speaker): texto):
{transcript_block}

Produce el JSON de analysis. Citas textuales exactas, evidencia semánticamente relevante."""
