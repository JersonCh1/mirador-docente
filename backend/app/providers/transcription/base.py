"""
Interfaz de proveedor de transcripción. Cualquier motor de ASR (AssemblyAI,
Whisper, Deepgram, fake...) implementa este contrato. Swappable por config.
"""
from __future__ import annotations

import abc


class TranscriptionProvider(abc.ABC):
    @abc.abstractmethod
    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe el audio en `audio_path`.

        Devuelve:
            {"segments": [{"speaker", "start", "end", "text"}, ...]}

        donde `speaker` está NORMALIZADO a "teacher" | "student",
        `start`/`end` en segundos (float) y `text` el texto del turno.
        """
        raise NotImplementedError
