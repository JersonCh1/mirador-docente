"""
Proveedor de transcripción WHISPER LOCAL (real, SIN API key) con faster-whisper.

Transcribe el audio REAL de la grabación en la propia máquina (CPU o GPU). No
inventa nada: si no hay audio o el paquete no está, falla con mensaje claro.

Diarización: faster-whisper NO separa hablantes por sí solo. Aquí usamos una
HEURÍSTICA honesta (no es diarización acústica): un turno corto en forma de
pregunta, o que interpela al docente ("profe…"), se etiqueta como `student`; el
resto como `teacher`. Es aproximada y está documentada como tal. Para diarización
real sin key alta-calidad, ver HANDOFF (whisperx/pyannote, requiere token HF).
"""
from __future__ import annotations

import os

from .base import TranscriptionProvider

try:
    from faster_whisper import WhisperModel  # type: ignore
except Exception:  # pragma: no cover - dependencia opcional
    WhisperModel = None


_VOCATIVES = ("profe", "profesor", "profesora", "maestro", "maestra", "teacher")


def _guess_speaker(text: str, duration: float) -> str:
    t = (text or "").strip().lower()
    looks_question = t.endswith("?") or t.startswith("¿")
    addresses_teacher = t.startswith(_VOCATIVES)
    if addresses_teacher or (looks_question and duration <= 12.0):
        return "student"
    return "teacher"


class WhisperTranscriptionProvider(TranscriptionProvider):
    def __init__(
        self,
        model_size: str = "small",
        language: str = "es",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        if WhisperModel is None:
            raise RuntimeError(
                "faster-whisper no está instalado. Ejecuta "
                "`pip install faster-whisper` o cambia TRANSCRIPTION_PROVIDER."
            )
        # La primera vez descarga el modelo (~150 MB para 'small'). Luego cachea.
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self._language = language

    def transcribe(self, audio_path: str) -> dict:
        if not audio_path or not os.path.exists(audio_path):
            raise RuntimeError(
                f"Audio/video no encontrado para transcribir: {audio_path!r}"
            )
        segments_iter, _info = self._model.transcribe(
            audio_path,
            language=self._language,
            vad_filter=True,  # recorta silencios → timestamps más limpios
        )
        segments = []
        for s in segments_iter:
            text = (s.text or "").strip()
            if not text:
                continue
            start = round(float(s.start), 2)
            end = round(float(s.end), 2)
            segments.append(
                {
                    "speaker": _guess_speaker(text, end - start),
                    "start": start,
                    "end": end,
                    "text": text,
                }
            )
        return {"segments": segments}
