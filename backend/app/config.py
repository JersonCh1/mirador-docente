"""
Configuración central de Mirador Docente.

Pydantic Settings leído desde variables de entorno (.env). Nada hardcodeado:
el default de proveedores es "fake" para que el MVP corra SIN API keys.
Cambiar de proveedor = cambiar UNA variable de entorno.
"""
from __future__ import annotations

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_FILLER_WORDS = [
    "o sea",
    "este",
    "¿no?",
    "eh",
    "mmm",
    "digamos",
    "entonces",
    "ya",
    "bueno",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Proveedores (swappables) ---
    TRANSCRIPTION_PROVIDER: str = "fake"  # fake | assemblyai
    LLM_PROVIDER: str = "fake"  # fake | claude

    # --- Keys (vacías por defecto: modo fake) ---
    ASSEMBLYAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # --- LLM ---
    LLM_MODEL: str = "claude-sonnet-4-6"
    LLM_TEMPERATURE: float = 0.2

    # --- Marcos pedagógicos activos (csv, en orden) ---
    ACTIVE_FRAMEWORKS: str = "minedu_mbdd,oecd_talis"

    # --- Métricas ---
    SILENCE_THRESHOLD: float = 8.0
    FILLER_WORDS: List[str] = DEFAULT_FILLER_WORDS

    # --- Infra ---
    DATABASE_URL: str = "sqlite:///./app.db"
    CORS_ORIGINS: str = "*"

    @field_validator("FILLER_WORDS", mode="before")
    @classmethod
    def _split_filler_words(cls, v):
        # Permite pasar la lista como csv en el .env o como lista en código.
        if isinstance(v, str):
            items = [w.strip() for w in v.split(",") if w.strip()]
            return items or DEFAULT_FILLER_WORDS
        return v

    @property
    def active_frameworks_list(self) -> List[str]:
        return [f.strip() for f in self.ACTIVE_FRAMEWORKS.split(",") if f.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        raw = self.CORS_ORIGINS.strip()
        if raw == "*" or not raw:
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    """Singleton de settings (cacheado)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
