"""
Proveedor LLM Groq (free tier). Usa la API OpenAI-compatible de Groq via httpx.
Si el modelo principal agota su cuota diaria, hace fallback automático a modelos
alternativos con cuotas independientes, y finalmente a Gemini si hay key.
"""
from __future__ import annotations

import time

import httpx

from .base import LLMProvider

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

# Groq: modelo principal primero, luego fallbacks.
_FALLBACK_MODELS = [
    ("llama-3.3-70b-versatile", 3000),
    ("llama-3.1-8b-instant",    1800),
    ("gemma2-9b-it",            1800),
]

# Gemini: 3.1-flash-lite tiene 500 RPD (250 sesiones/día), ideal para respaldo.
_GEMINI_FALLBACK_MODELS = [
    ("gemini-3.1-flash-lite", 2000),
    ("gemini-2.5-flash-lite", 2000),
]


class GroqProvider(LLMProvider):

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.2,
        max_tokens: int = 3000,
        gemini_api_key: str = "",
    ):
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY no configurada. Usa LLM_PROVIDER=fake para el "
                "modo demo, o provee la key real de groq.com (gratis)."
            )
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._gemini_api_key = gemini_api_key

    def _call_openai_compat(
        self,
        url: str,
        api_key: str,
        model: str,
        prompt: str,
        max_tokens: int,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        for attempt in range(3):
            resp = httpx.post(url, headers=headers, json=body, timeout=120.0)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", 65))
                if retry_after > 120:
                    raise _QuotaExhausted(model, retry_after)
                wait = max(retry_after, 10)
                print(f"[LLM/{model}] Rate limit — esperando {wait}s (intento {attempt+1}/3)…")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def complete(self, prompt: str) -> str:
        # 1. Intenta modelos Groq en cascada.
        primary = (self._model, self._max_tokens)
        others = [(m, t) for m, t in _FALLBACK_MODELS if m != self._model]
        for model, max_tok in [primary] + others:
            try:
                result = self._call_openai_compat(_GROQ_URL, self._api_key, model, prompt, max_tok)
                if model != self._model:
                    print(f"[Groq] Usando fallback: {model}")
                return result
            except _QuotaExhausted:
                print(f"[Groq] Cuota agotada para {model}, probando siguiente…")

        # 2. Intenta modelos Gemini si hay key.
        if self._gemini_api_key:
            for g_model, g_tok in _GEMINI_FALLBACK_MODELS:
                try:
                    print(f"[Gemini] Groq agotado — usando {g_model}…")
                    return self._call_openai_compat(
                        _GEMINI_URL, self._gemini_api_key, g_model, prompt, g_tok
                    )
                except _QuotaExhausted:
                    print(f"[Gemini] Cuota agotada para {g_model}, probando siguiente…")

        raise RuntimeError(
            "Todos los modelos de Groq y Gemini tienen cuota agotada. "
            "Intenta en unos minutos o revisa tus límites en groq.com / aistudio.google.com"
        )


class _QuotaExhausted(Exception):
    def __init__(self, model: str, retry_after: int):
        self.model = model
        self.retry_after = retry_after
        super().__init__(f"{model}: cuota agotada, retry-after={retry_after}s")
