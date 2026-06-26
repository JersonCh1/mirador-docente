"""
Muestreo de frames de video → `visual_timeline` del contrato.

ESTADO: seam conectado al pipeline (etapa 4), pero la implementación visual aún
NO está hecha: devuelve [] de forma honesta (no se inventan segmentos).

Cómo completarlo (para la próxima sesión) — ver HANDOFF_NEXT_SESSION.md §Frames:
  1. ffprobe para la duración del video.
  2. ffmpeg con el filtro `select='gt(scene,0.4)'` para sacar frames en cambios
     de escena (o 1 frame cada `every_seconds`).
  3. Clasificar cada frame con Claude multimodal (visión) en uno de:
     slides | whiteboard | screen_share | none.
  4. Colapsar frames consecutivos del mismo tipo en segmentos {start,end,type}.

Mientras no esté: el contrato permite `visual_timeline: []` y la cinta del
frontend muestra solo las anclas de evidencia. Es comportamiento válido del MVP.
"""
from __future__ import annotations

import os
import shutil


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def sample_frames(video_path: str | None, every_seconds: float = 30.0) -> list:
    """
    Devuelve la `visual_timeline`: lista de {start, end, type}.

    Hoy devuelve [] (sin análisis visual). NO inventa segmentos: si no hay video
    local o no hay ffmpeg, devuelve [] de inmediato. El punto de extensión está
    documentado arriba.
    """
    if not video_path or not os.path.exists(video_path) or not _has_ffmpeg():
        return []
    # TODO(visión): implementar muestreo + clasificación multimodal.
    return []
