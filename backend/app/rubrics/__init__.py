"""
Registry de marcos pedagógicos pluggables.

Fuentes (en orden de prioridad):
  1. Built-in del código (`minedu_mbdd`, `oecd_talis`) — fallback.
  2. JSON de la carpeta de estándares (`settings.standards_dir`), que
     SOBRESCRIBE al built-in con el mismo framework_id. Esa carpeta es la
     fuente de verdad editable: ver `backend/standards/README.md`.

Agregar/corregir un marco = soltar/editar un JSON en esa carpeta. Sin tocar el
motor. Un JSON inválido se ignora (nunca crashea el server).
"""
from __future__ import annotations

import json
import os

from ..config import Settings, get_settings
from .minedu_mbdd import FRAMEWORK as MINEDU_MBDD
from .oecd_talis import FRAMEWORK as OECD_TALIS

# Marcos built-in (fallback si la carpeta de estándares está vacía).
_BUILTINS: dict[str, dict] = {
    MINEDU_MBDD["framework_id"]: MINEDU_MBDD,
    OECD_TALIS["framework_id"]: OECD_TALIS,
}

_REGISTRY_CACHE: dict[str, dict] | None = None


def _valid_framework(obj) -> bool:
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("framework_id"), str)
        and isinstance(obj.get("framework_name"), str)
        and isinstance(obj.get("dimensions"), list)
    )


def _load_from_dir(path: str) -> dict[str, dict]:
    """Carga los *.json válidos de la carpeta de estándares, ignorando los rotos."""
    out: dict[str, dict] = {}
    if not path or not os.path.isdir(path):
        return out
    for name in sorted(os.listdir(path)):
        if not name.lower().endswith(".json"):
            continue
        try:
            with open(os.path.join(path, name), encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue  # archivo inválido => se ignora, nunca crashea
        if _valid_framework(data):
            out[data["framework_id"]] = data
    return out


def build_registry(settings: Settings | None = None) -> dict[str, dict]:
    """Construye (y cachea) el registro: built-ins + JSON de la carpeta de estándares."""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE
    settings = settings or get_settings()
    registry = dict(_BUILTINS)
    registry.update(_load_from_dir(settings.standards_dir))  # el disco manda
    _REGISTRY_CACHE = registry
    return registry


def reload_registry() -> None:
    """Invalida la caché del registro (útil tras editar la carpeta de estándares)."""
    global _REGISTRY_CACHE
    _REGISTRY_CACHE = None


# Vista del registro (built-ins + estándares en disco) para compatibilidad.
REGISTRY = build_registry()


def get_active_frameworks(settings: Settings | None = None) -> list[dict]:
    """Devuelve los marcos activos (ACTIVE_FRAMEWORKS csv) en orden, ignorando ids desconocidos."""
    settings = settings or get_settings()
    registry = build_registry(settings)
    out = []
    for fid in settings.active_frameworks_list:
        fw = registry.get(fid)
        if fw is not None:
            out.append(fw)
    return out
