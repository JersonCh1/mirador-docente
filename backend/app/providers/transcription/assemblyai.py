"""
Proveedor de transcripción AssemblyAI (real). Usa el SDK `assemblyai` con
diarización (speaker_labels) y español. Heurística de etiquetado: el speaker con
MAYOR tiempo total de habla es el "teacher"; los demás son "student".

El import del SDK va envuelto en try/except para que la ausencia del paquete NO
rompa el arranque del server (en modo fake no se necesita).
"""
from __future__ import annotations

from collections import defaultdict

from .base import TranscriptionProvider

try:
    import assemblyai as aai  # type: ignore
except Exception:  # pragma: no cover - SDK opcional
    aai = None


class AssemblyAIProvider(TranscriptionProvider):
    def __init__(self, api_key: str, language_code: str = "es"):
        if not api_key:
            raise RuntimeError(
                "ASSEMBLYAI_API_KEY no configurada. Usa TRANSCRIPTION_PROVIDER=fake "
                "para el modo demo sin keys, o provee la key real."
            )
        if aai is None:
            raise RuntimeError(
                "El paquete 'assemblyai' no está instalado. Ejecuta "
                "`pip install assemblyai` o usa TRANSCRIPTION_PROVIDER=fake."
            )
        self._api_key = api_key
        self._language_code = language_code
        aai.settings.api_key = api_key

    def transcribe(self, audio_path: str) -> dict:
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            language_code=self._language_code,
        )
        transcript = aai.Transcriber().transcribe(audio_path, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI falló: {transcript.error}")

        utterances = transcript.utterances or []
        if not utterances:
            return {"segments": []}

        # Tiempo total de habla por speaker (ms) → el de más tiempo = teacher.
        totals: dict[str, float] = defaultdict(float)
        for u in utterances:
            totals[u.speaker] += (u.end - u.start)
        teacher_speaker = max(totals, key=totals.get)

        segments = []
        for u in utterances:
            segments.append(
                {
                    "speaker": "teacher" if u.speaker == teacher_speaker else "student",
                    "start": round(u.start / 1000.0, 2),  # ms → s
                    "end": round(u.end / 1000.0, 2),
                    "text": (u.text or "").strip(),
                }
            )
        return {"segments": segments}
