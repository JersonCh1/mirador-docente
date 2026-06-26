"""
Factory de proveedores. Lee la config y devuelve la implementación concreta de
transcripción / LLM. Cambiar de proveedor = cambiar una variable de entorno.
"""
from __future__ import annotations

from ..config import Settings, get_settings
from .llm.base import LLMProvider
from .transcription.base import TranscriptionProvider


def get_transcription_provider(settings: Settings | None = None) -> TranscriptionProvider:
    settings = settings or get_settings()
    provider = (settings.TRANSCRIPTION_PROVIDER or "fake").lower()

    if provider == "fake":
        from .transcription.fake import FakeTranscriptionProvider

        return FakeTranscriptionProvider()
    if provider == "assemblyai":
        from .transcription.assemblyai import AssemblyAIProvider

        return AssemblyAIProvider(api_key=settings.ASSEMBLYAI_API_KEY)
    if provider == "whisper":
        # Local, real, SIN API key (faster-whisper).
        from .transcription.whisper import WhisperTranscriptionProvider

        return WhisperTranscriptionProvider(
            model_size=settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )

    raise ValueError(f"TRANSCRIPTION_PROVIDER desconocido: {provider!r}")


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider = (settings.LLM_PROVIDER or "fake").lower()

    if provider == "fake":
        from .llm.fake import FakeLLMProvider

        return FakeLLMProvider()
    if provider == "claude":
        from .llm.claude import ClaudeProvider

        return ClaudeProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )
    if provider == "ollama":
        # Local, real, SIN API key (servidor de Ollama).
        from .llm.ollama import OllamaProvider

        return OllamaProvider(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
        )
    if provider == "groq":
        from .llm.groq import GroqProvider

        return GroqProvider(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )

    raise ValueError(f"LLM_PROVIDER desconocido: {provider!r}")
