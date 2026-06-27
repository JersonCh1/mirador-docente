"""
Proveedor LLM Groq (free tier). Usa la API OpenAI-compatible de Groq via httpx.
Si el modelo principal agota su cuota diaria, hace fallback automático a modelos
alternativos con cuotas independientes.
"""
from __future__ import annotations

import time

import httpx

from .base import LLMProvider

# Modelos en orden de preferencia con sus max_tokens seguros.
# El 8B y gemma tienen límite de ~6k tokens por request, así que reducimos output.
_FALLBACK_MODELS = [
    ("llama-3.3-70b-versatile", 3000),
    ("llama-3.1-8b-instant",    1800),
    ("gemma2-9b-it",            1800),
]


class GroqProvider(LLMProvider):
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.2,
        max_tokens: int = 3000,
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

    def _call_with_tokens(self, model: str, max_tokens: int, prompt: str) -> str:
        return self._call(model, prompt, max_tokens)

    def _call(self, model: str, prompt: str, max_tokens: int | None = None) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": max_tokens if max_tokens is not None else self._max_tokens,
            "response_format": {"type": "json_object"},
        }
        for attempt in range(3):
            resp = httpx.post(self.BASE_URL, headers=headers, json=body, timeout=120.0)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("retry-after", 65))
                if retry_after > 120:
                    # Cuota diaria agotada para este modelo.
                    raise _QuotaExhausted(model, retry_after)
                wait = max(retry_after, 10)
                print(f"[Groq/{model}] Rate limit — esperando {wait}s (intento {attempt+1}/3)…")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            break
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def complete(self, prompt: str) -> str:
        # Construye lista de modelos: el configurado primero, luego fallbacks.
        primary = (self._model, self._max_tokens)
        others = [(m, t) for m, t in _FALLBACK_MODELS if m != self._model]
        models_to_try = [primary] + others
        last_err: Exception = RuntimeError("Sin modelos disponibles")
        for model, max_tok in models_to_try:
            try:
                result = self._call_with_tokens(model, max_tok, prompt)
                if model != self._model:
                    print(f"[Groq] Usando fallback: {model}")
                return result
            except _QuotaExhausted as e:
                print(f"[Groq] Cuota agotada para {model}, probando siguiente…")
                last_err = e
                continue
        raise RuntimeError(
            f"Todos los modelos de Groq tienen cuota agotada. {last_err}"
        )


class _QuotaExhausted(Exception):
    def __init__(self, model: str, retry_after: int):
        self.model = model
        self.retry_after = retry_after
        super().__init__(f"{model}: cuota agotada, retry-after={retry_after}s")
