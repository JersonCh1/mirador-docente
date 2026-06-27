"""
Construcción del prompt de análisis pedagógico. El LLM actúa como evaluador
experto y DEBE anclar cada juicio en evidencia textual con timestamp.
"""
from __future__ import annotations

import json

# Groq free tier: 12k TPM. Budget: ~5k input + 3k output = 8k, margen seguro.
# Reducimos transcript y enviamos frameworks sin campos verbosos (source/description).
_MAX_TRANSCRIPT_CHARS = 8_000    # límite total del bloque de transcript
_WINDOW_SECS = 180               # ventana de tiempo: cada 3 minutos, 1 muestra
_CHARS_PER_WINDOW = 300          # chars que se muestran por ventana


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


def _slim_frameworks(frameworks: list[dict]) -> list[dict]:
    """Elimina source/description de los frameworks para reducir tokens.
    El LLM solo necesita name + look_for para saber qué evaluar."""
    slim = []
    for fw in frameworks:
        slim.append({
            "framework_id": fw["framework_id"],
            "framework_name": fw["framework_name"],
            "dimensions": [
                {
                    "dimension_id": d["dimension_id"],
                    "name": d["name"],
                    "look_for": d.get("look_for", ""),
                    "observable_from_recording": d.get("observable_from_recording", True),
                }
                for d in fw.get("dimensions", [])
            ],
        })
    return slim


def build_prompt(
    transcript: dict,
    metrics: dict,
    frameworks: list[dict],
    objectives: list[str] | None,
    include_global: bool = True,
) -> str:
    frameworks_json = json.dumps(_slim_frameworks(frameworks), ensure_ascii=False, indent=2)
    metrics_json = json.dumps(metrics, ensure_ascii=False)
    objectives_json = json.dumps(objectives or [], ensure_ascii=False)
    transcript_block = _transcript_lines(transcript)

    total_mins = (transcript or {}).get('segments', [{}])[-1].get('end', 0) / 60
    third = total_mins / 3

    global_rules = """
5. FORTALEZAS (mín. 3) — ejemplos del tono esperado:
   "Hiciste muy bien en abrir con una pregunta que conecta el derecho con la vida cotidiana"
   "En el minuto 34 cuando pediste a los estudiantes que definieran justicia, lograste..."

6. MEJORAS (mín. 3) — ejemplos del tono esperado:
   "En la segunda mitad de la clase, podrías haber pausado para preguntar si todos seguían"
   "Te sugiero que en la próxima clase incluyas un momento donde los estudiantes..."
   Cada mejora lleva una `suggestion` concreta: qué hacer diferente y cómo.
""" if include_global else "5. NO incluyas fortalezas ni mejoras globales en esta llamada.\n"

    global_schema = """
  "strengths": [{"title": "<elogio directo>", "detail": "<con minuto concreto>", "timestamp": <float>}],
  "improvements": [{"title": "<área de mejora>", "detail": "<qué observaste>", "timestamp": <float>, "suggestion": "<qué hacer diferente>"}],
  "objective_alignment": {"aligned_pct": <0-1>, "deviations": [{"start": <float>, "end": <float>, "note": "..."}]} | null""" if include_global else """
  "strengths": [],
  "improvements": [],
  "objective_alignment": null"""

    return f"""Eres un coach pedagógico experto. Acabas de observar la clase completa de
un docente y ahora le das retroalimentación DIRECTA Y PERSONAL, hablándole de TÚ,
como si estuvieras sentado frente a él/ella después de ver la grabación.

TONO OBLIGATORIO:
- SEGUNDA PERSONA SINGULAR: "hiciste", "lograste", "podrías", "te sugiero".
- MOMENTOS CONCRETOS: "En el minuto X, cuando dijiste '...' hiciste muy bien..."
- PROHIBIDO tercera persona ("el docente", "se observa que").

REGLAS DE ANÁLISIS:

1. COBERTURA TOTAL — clase de {total_mins:.0f} min dividida en:
   - INICIO (min 0–{third:.0f}), DESARROLLO (min {third:.0f}–{third*2:.0f}), CIERRE (min {third*2:.0f}–{total_mins:.0f}).
   MÍNIMO 1 evidencia por dimensión de cada tercio. No concentres todo al inicio.

2. CITA TEXTUAL EXACTA copiada del transcript. Solo citas semánticamente relevantes a la dimensión.

3. SCORES HONESTOS 1–4. overall_score = promedio de dimensiones observables.

4. DIMENSIONES NO OBSERVABLES → observable: false, score: null, evidence: [].
{global_rules}
7. SALIDA: ÚNICAMENTE JSON válido, sin markdown ni texto extra.

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
          "summary": "<1-2 oraciones en segunda persona sobre ESTA clase>",
          "evidence": [{{"timestamp": <float>, "quote": "<cita exacta>", "comment": "<por qué evidencia la dimensión>"}}]
        }}
      ]
    }}
  ],{global_schema}
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
