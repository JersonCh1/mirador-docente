"""
Respuesta de emergencia cuando todos los modelos de Groq tienen cuota agotada.
Lee directamente los datos de la sesión sin llamar al LLM.
"""
from __future__ import annotations

from .tools import get_analysis, get_metrics, search_transcript


def static_reply(session: dict, user_message: str) -> str:
    """Responde a partir de los datos crudos cuando el LLM no está disponible."""
    q = user_message.lower()

    # Detecta qué datos son más relevantes para la pregunta
    wants_metric = any(w in q for w in ["tiempo", "minuto", "habla", "silencio", "duración", "porcentaje", "estadística", "cuánto"])
    wants_transcript = any(w in q for w in ["dije", "dijiste", "transcript", "cité", "cita", "exactamente", "momento", "cuándo", "mencioné"])
    wants_score = any(w in q for w in ["score", "puntaje", "nota", "dimensión", "resultado", "calificación", "evaluación", "framework"])

    parts = []
    parts.append("⚠️ *El servicio de IA está temporalmente saturado. Te muestro los datos directamente:*\n")

    if wants_metric or (not wants_transcript and not wants_score):
        metrics = get_metrics(session)
        if metrics and "No hay" not in metrics:
            parts.append("**Métricas de tu clase:**\n" + metrics)

    if wants_transcript:
        # Extrae palabras clave de la pregunta para buscar
        stopwords = {"qué", "cuándo", "dije", "dijiste", "exactamente", "momento", "sobre", "la", "el", "en", "de", "que", "me", "mi"}
        keywords = [w for w in q.split() if len(w) > 3 and w not in stopwords]
        if keywords:
            for kw in keywords[:2]:
                result = search_transcript(session, kw, max_results=3)
                if "No se encontraron" not in result:
                    parts.append(f"\n**En el transcript ({kw}):**\n" + result)
                    break
            else:
                parts.append("\n" + get_analysis(session))
        else:
            parts.append("\n" + get_analysis(session))
    else:
        parts.append("\n**Análisis completo de tu clase:**\n" + get_analysis(session))

    parts.append("\n\n*Intenta de nuevo en unos minutos para obtener una respuesta conversacional del coach.*")
    return "\n".join(parts)
