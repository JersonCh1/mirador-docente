"""
Registry de marcos pedagógicos pluggables. Agregar un marco = agregar un módulo
con su FRAMEWORK (datos) y registrarlo en REGISTRY. Sin tocar el motor.
"""
from __future__ import annotations

from ..config import Settings, get_settings
from .minedu_mbdd import FRAMEWORK as MINEDU_MBDD
from .oecd_talis import FRAMEWORK as OECD_TALIS

REGISTRY: dict[str, dict] = {
    MINEDU_MBDD["framework_id"]: MINEDU_MBDD,
    OECD_TALIS["framework_id"]: OECD_TALIS,
}


def get_active_frameworks(settings: Settings | None = None) -> list[dict]:
    """Devuelve los marcos activos (ACTIVE_FRAMEWORKS csv) en orden, ignorando ids desconocidos."""
    settings = settings or get_settings()
    out = []
    for fid in settings.active_frameworks_list:
        fw = REGISTRY.get(fid)
        if fw is not None:
            out.append(fw)
    return out
