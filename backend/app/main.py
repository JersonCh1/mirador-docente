"""
App FastAPI de Mirador Docente. Monta el router /api, configura CORS desde
config e inicializa la DB en el arranque. En producción (un solo servicio
Railway) sirve el build del frontend desde `frontend/dist` si existe.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.sessions import router as sessions_router
from .config import get_settings
from .db import init_db

settings = get_settings()

app = FastAPI(title="Mirador Docente API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router, prefix="/api")


@app.on_event("startup")
def _on_startup() -> None:
    init_db()


# --- Servir el frontend buildeado (opcional, solo si existe) --------------- #
# backend/app/main.py → sube a la raíz del repo → frontend/dist
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_FRONTEND_DIST = os.path.join(_REPO_ROOT, "frontend", "dist")

if os.path.isdir(_FRONTEND_DIST):
    _assets = os.path.join(_FRONTEND_DIST, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    _index = os.path.join(_FRONTEND_DIST, "index.html")

    @app.get("/")
    def _spa_root() -> FileResponse:
        return FileResponse(_index)

    @app.get("/{full_path:path}")
    def _spa_fallback(full_path: str) -> FileResponse:
        # Sirve archivos estáticos reales si existen; si no, index.html (SPA).
        candidate = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(_index)
