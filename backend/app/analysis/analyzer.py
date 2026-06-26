"""
Analyzer: orquesta la llamada al LLM para producir el `analysis` anclado en
evidencia. Limpia fences, parsea JSON y reintenta UNA vez ante fallo de parseo.
"""
from __future__ import annotations

import json
import re

from ..providers.llm.base import LLMProvider
from .prompt import build_prompt


def _strip_fences(text: str) -> str:
    """Quita ```json ... ``` o ``` ... ``` si el modelo los incluye."""
    t = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", t, flags=re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return t


def _extract_json(text: str) -> str:
    """Recorta hasta el primer '{' y el último '}' por si hay texto alrededor."""
    cleaned = _strip_fences(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


class Analyzer:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def analyze(
        self,
        transcript: dict,
        metrics: dict,
        frameworks: list[dict],
        objectives: list[str] | None,
    ) -> dict:
        prompt = build_prompt(transcript, metrics, frameworks, objectives)

        raw = self.llm.complete(prompt)
        parsed = self._try_parse(raw)
        if parsed is not None:
            return parsed

        # Reintento único con mensaje correctivo.
        corrective = (
            prompt
            + "\n\nIMPORTANTE: tu respuesta anterior NO fue JSON válido. "
            "Responde ÚNICAMENTE con el objeto JSON de 'analysis', sin markdown, "
            "sin fences y sin ningún texto adicional."
        )
        raw2 = self.llm.complete(corrective)
        parsed2 = self._try_parse(raw2)
        if parsed2 is not None:
            return parsed2

        raise ValueError(
            "El LLM no devolvió un JSON de 'analysis' parseable tras un reintento."
        )

    @staticmethod
    def _try_parse(raw: str) -> dict | None:
        try:
            data = json.loads(_extract_json(raw))
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(data, dict) or "frameworks" not in data:
            return None
        return data
