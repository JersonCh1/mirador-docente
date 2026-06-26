"""
Proveedor LLM Groq (free tier). Usa la API OpenAI-compatible de Groq via httpx.
Modelo por defecto: llama-3.1-70b-versatile (gratis, muy capaz para JSON estructurado).
"""
from __future__ import annotations

import json

import httpx

from .base import LLMProvider


class GroqProvider(LLMProvider):
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.2,
        max_tokens: int = 5000,
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

    def complete(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        resp = httpx.post(
            self.BASE_URL,
            headers=headers,
            json=body,
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
