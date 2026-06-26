"""
Extracción de audio con ffmpeg vía subprocess. Sin librerías pesadas.
Maneja con gracia la ausencia de ffmpeg y los inputs que ya son audio.
"""
from __future__ import annotations

import os
import shutil
import subprocess

_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_audio(input_path: str, output_path: str) -> str:
    """
    Extrae pista de audio mono a 16 kHz WAV con ffmpeg.

    - Si el input ya es un archivo de audio, lo devuelve tal cual.
    - Si ffmpeg no está disponible, devuelve el input (degradación elegante;
      los proveedores de transcripción reales fallarán con mensaje claro, el
      FakeProvider ignora el audio).
    """
    if not input_path or not os.path.exists(input_path):
        # Nada que extraer (p.ej. sesión creada desde URL sin descarga).
        return input_path

    ext = os.path.splitext(input_path)[1].lower()
    if ext in _AUDIO_EXTS:
        return input_path

    if not _has_ffmpeg():
        return input_path

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vn",            # sin video
        "-ac", "1",       # mono
        "-ar", "16000",   # 16 kHz
        output_path,
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg falló al extraer audio: {stderr[-500:]}") from e

    return output_path
