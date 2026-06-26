"""
Proveedor LLM Claude (real) usando el SDK `anthropic`. Modelo y temperatura
vienen de config. El import del SDK va en try/except para no romper el arranque
en modo fake.
"""
from __future__ import annotations

from .base import LLMProvider

try:
    import anthropic  # type: ignore
except Exception:  # pragma: no cover - SDK opcional
    anthropic = None


class ClaudeProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        temperature: float = 0.2,
        max_tokens: int = 8000,
    ):
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY no configurada. Usa LLM_PROVIDER=fake para el "
                "modo demo sin keys, o provee la key real."
            )
        if anthropic is None:
            raise RuntimeError(
                "El paquete 'anthropic' no está instalado. Ejecuta "
                "`pip install anthropic` o usa LLM_PROVIDER=fake."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def complete(self, prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        # Concatena todos los bloques de texto de la respuesta.
        parts = []
        for block in resp.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts).strip()
