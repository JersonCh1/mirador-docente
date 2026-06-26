"""
Interfaz de proveedor LLM. Cualquier modelo (Claude, GPT, Gemini, fake...)
implementa `complete(prompt) -> str`. Swappable por config.
"""
from __future__ import annotations

import abc


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def complete(self, prompt: str) -> str:
        """Recibe un prompt completo y devuelve el texto de la respuesta."""
        raise NotImplementedError
