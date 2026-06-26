"""
Proveedor LLM OLLAMA LOCAL (real, SIN API key). Habla por HTTP con el servidor
de Ollama (por defecto http://localhost:11434). Modelo configurable.

Análisis REAL del transcript real, en tu máquina, sin pagar nada. Requiere tener
Ollama corriendo (`ollama serve`) y el modelo descargado (`ollama pull llama3.1`).
`format=json` fuerza salida JSON válida, que es justo lo que el Analyzer parsea.
"""
from __future__ import annotations

import httpx

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.2,
        timeout: float = 600.0,
    ):
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._temperature = temperature
        self._timeout = timeout

    def complete(self, prompt: str) -> str:
        try:
            resp = httpx.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # salida JSON válida para el Analyzer
                    "options": {"temperature": self._temperature},
                },
                timeout=self._timeout,
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(
                f"No se pudo contactar Ollama en {self._base_url}. ¿Está corriendo "
                f"`ollama serve` y descargado el modelo '{self._model}' "
                f"(`ollama pull {self._model}`)? Detalle: {e}"
            ) from e
        return (resp.json().get("response") or "").strip()
