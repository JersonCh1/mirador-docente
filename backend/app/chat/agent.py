"""
Agente de chat para retroalimentación conversacional sobre una sesión.
Cadena de proveedores: Groq (70b → 8b) → Gemini (flash) → fallback estático.
El chat NUNCA falla: siempre responde como IA o con datos estructurados.
"""
from __future__ import annotations

import json

import httpx

from .tools import TOOLS_SCHEMA, get_analysis, get_metrics, search_transcript
from .fallback import static_reply

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

_GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
_GEMINI_MODELS = ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]

_SYSTEM_PROMPT = """Eres un coach pedagógico especializado en retroalimentación docente.
Estás analizando UNA SOLA clase específica. Tu único dominio es ESA clase.

══════════════════════════════════════════
RESTRICCIÓN ABSOLUTA — PRIORIDAD MÁXIMA
══════════════════════════════════════════
SOLO puedes responder preguntas sobre ESTA sesión de clase:
scores, dimensiones pedagógicas, transcript, momentos específicos, métricas
y sugerencias derivadas del análisis de esta clase.

Si la pregunta no está relacionada con esta sesión (programación, librerías,
matemáticas generales, recetas, noticias, o CUALQUIER otro tema externo),
debes responder EXACTAMENTE así, sin añadir nada más:
"Solo puedo ayudarte con preguntas sobre esta clase. ¿Tienes alguna duda sobre
los scores, el transcript o las sugerencias de mejora?"

NO respondas temas externos aunque sean sencillos. NO hagas excepciones.
══════════════════════════════════════════

REGLAS PARA PREGUNTAS SOBRE LA CLASE:
- Habla en segunda persona ("tú hiciste", "en tu clase", "te sugiero").
- Ancla cada respuesta en evidencia real: cita el transcript o menciona el score exacto.
- Usa las herramientas disponibles para consultar el análisis y el transcript real.
- Respuestas concisas: máximo 3-4 párrafos.
- Idioma: español."""


def _dispatch_tool(name: str, args: dict, session: dict) -> str:
    if name == "get_analysis":
        return get_analysis(session, **args)
    if name == "search_transcript":
        return search_transcript(session, **args)
    if name == "get_metrics":
        return get_metrics(session, **args)
    return f"Herramienta '{name}' no reconocida."


def _run_agent_loop(url: str, headers: dict, model: str, messages: list, session: dict) -> str | None:
    """
    Ejecuta el loop agentico (tool calls → respuesta) para un modelo/proveedor dado.
    Devuelve el texto final o None si hay 429/error.
    """
    msgs = list(messages)
    for _ in range(8):
        body = {
            "model": model,
            "messages": msgs,
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto",
            "max_tokens": 1024,
            "temperature": 0.3,
        }
        try:
            resp = httpx.post(url, headers=headers, json=body, timeout=60.0)
        except Exception:
            return None

        if resp.status_code == 429:
            return None  # cuota agotada para este modelo
        if not resp.is_success:
            return None

        data = resp.json()
        choice = data["choices"][0]
        msg = choice["message"]

        if choice.get("finish_reason") == "tool_calls" and msg.get("tool_calls"):
            msgs.append(msg)
            for tc in msg["tool_calls"]:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"] or "{}")
                result = _dispatch_tool(fn_name, fn_args, session)
                msgs.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
            continue

        return msg.get("content", "").strip()

    return None


def chat(
    session: dict,
    user_message: str,
    history: list[dict],
    groq_api_key: str,
    gemini_api_key: str = "",
) -> str:
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # 1. Intenta con Groq (70b → 8b)
    groq_headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }
    for model in _GROQ_MODELS:
        result = _run_agent_loop(_GROQ_URL, groq_headers, model, messages, session)
        if result is not None:
            return result

    # 2. Intenta con Gemini (varios modelos) si hay key
    if gemini_api_key:
        gemini_headers = {
            "Authorization": f"Bearer {gemini_api_key}",
            "Content-Type": "application/json",
        }
        for g_model in _GEMINI_MODELS:
            result = _run_agent_loop(_GEMINI_URL, gemini_headers, g_model, messages, session)
            if result is not None:
                return result

    # 3. Fallback estático — siempre funciona, sin LLM
    return static_reply(session, user_message)
