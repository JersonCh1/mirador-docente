"""
Analyzer: orquesta la llamada al LLM para producir el `analysis` anclado en
evidencia. Limpia fences/<think>, parsea JSON y reintenta UNA vez ante fallo.
"""
from __future__ import annotations

import json
import re

from ..providers.llm.base import LLMProvider
from .prompt import build_prompt


def _clean_llm_output(text: str) -> str:
    """Quita <think>...</think>, fences y cualquier texto fuera del JSON."""
    t = text.strip()
    # Algunos modelos (qwen, deepseek) emiten <think>...</think> antes del JSON.
    t = re.sub(r"<think>.*?</think>", "", t, flags=re.DOTALL).strip()
    # Quita ```json ... ``` o ``` ... ```
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", t, flags=re.DOTALL)
    if fence:
        t = fence.group(1).strip()
    # Recorta al primer '{' y último '}' por si hay texto alrededor.
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]
    return t


class Analyzer:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def analyze(
        self,
        transcript: dict,
        metrics: dict,
        frameworks: list[dict],
        objectives: list[str] | None,
        include_global: bool = True,
    ) -> dict:
        prompt = build_prompt(transcript, metrics, frameworks, objectives, include_global=include_global)

        raw = self.llm.complete(prompt)
        parsed = self._try_parse(raw)
        if parsed is not None:
            return parsed

        # Reintento ligero: solo pide el JSON sin reenviar el prompt completo.
        fix_prompt = (
            "El siguiente texto debería ser un JSON válido pero tiene errores. "
            "Devuelve ÚNICAMENTE el objeto JSON corregido y completo, sin markdown:\n\n"
            + raw[:4000]
        )
        raw2 = self.llm.complete(fix_prompt)
        parsed2 = self._try_parse(raw2)
        if parsed2 is not None:
            return parsed2

        raise ValueError(
            "El LLM no devolvió un JSON de 'analysis' parseable tras un reintento."
        )

    @staticmethod
    def _try_parse(raw: str) -> dict | None:
        try:
            data = json.loads(_clean_llm_output(raw))
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(data, dict) or "frameworks" not in data:
            return None
        return data
