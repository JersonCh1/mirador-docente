"""
Proveedor LLM FAKE. Devuelve un JSON string con EXACTAMENTE la sub-estructura
"analysis" del mock canónico (`frontend/src/mocks/sample_session.json`). Así el
paso de análisis funciona end-to-end SIN key de Claude.

El analizador pide el análisis por marco; este fake devuelve el análisis COMPLETO
(ambos marcos + strengths + improvements + objective_alignment) y el pipeline se
encarga de seleccionar el marco pedido en cada iteración. Si cambias esto, rompes
la paridad con el mock del frontend.
"""
from __future__ import annotations

import json

from .base import LLMProvider

# Copia textual de la clave "analysis" del mock canónico.
_ANALYSIS = {
    "frameworks": [
        {
            "framework_id": "minedu_mbdd",
            "framework_name": "Marco de Buen Desempeño Docente (MINEDU)",
            "overall_score": 3.0,
            "dimensions": [
                {
                    "dimension_id": "dominio_disciplinar",
                    "name": "Claridad y dominio disciplinar en la conducción de la clase",
                    "score": 4,
                    "max_score": 4,
                    "observable": True,
                    "summary": "Explicaciones precisas y bien estructuradas, con analogías que conectan el concepto abstracto con la intuición física.",
                    "evidence": [
                        {"timestamp": 20.0, "quote": "La derivada mide la razón de cambio instantánea de una función. Piensen en la velocidad de un auto en un instante exacto, no en el promedio del viaje.", "comment": "Analogía clara que aterriza un concepto abstracto."},
                        {"timestamp": 64.5, "quote": "Exacto, muy buena observación. La derivada en un punto es precisamente la pendiente de la recta tangente a la curva en ese punto.", "comment": "Refuerza y valida la intervención del estudiante con precisión."},
                    ],
                },
                {
                    "dimension_id": "activacion_cognitiva",
                    "name": "Estrategias que promueven el razonamiento y el pensamiento crítico",
                    "score": 2,
                    "max_score": 4,
                    "observable": True,
                    "summary": "Lanza preguntas que invitan a razonar, pero con frecuencia no espera la respuesta y él mismo la contesta, cerrando la oportunidad de pensamiento.",
                    "evidence": [
                        {"timestamp": 240.0, "quote": "Ahora, ¿alguien me puede decir qué pasa con la derivada cuando la función es constante?", "comment": "Buena pregunta abierta..."},
                        {"timestamp": 263.0, "quote": "Bueno, sigamos, la derivada de una constante es cero porque no hay cambio.", "comment": "...pero la responde él mismo sin dar tiempo a los estudiantes."},
                    ],
                },
                {
                    "dimension_id": "verificacion_comprension",
                    "name": "Uso de la evaluación y verificación de comprensión durante la sesión",
                    "score": 3,
                    "max_score": 4,
                    "observable": True,
                    "summary": "Verifica comprensión en momentos clave, aunque las preguntas de chequeo son cerradas y no garantizan que todos hayan entendido.",
                    "evidence": [
                        {"timestamp": 1394.0, "quote": "¿Todos de acuerdo hasta aquí? Perfecto, avancemos entonces con un ejercicio más difícil.", "comment": "Chequeo de comprensión de tipo sí/no; no diagnostica comprensión real."},
                    ],
                },
                {
                    "dimension_id": "clima_aula",
                    "name": "Clima de aula: respeto, motivación y manejo de la participación",
                    "score": 3,
                    "max_score": 4,
                    "observable": True,
                    "summary": "Trato cálido y respetuoso; refuerza positivamente las intervenciones de los estudiantes cuando ocurren.",
                    "evidence": [
                        {"timestamp": 64.5, "quote": "Exacto, muy buena observación. La derivada en un punto es precisamente la pendiente de la recta tangente a la curva en ese punto.", "comment": "Refuerzo positivo explícito a la participación."},
                    ],
                },
                {
                    "dimension_id": "planificacion_curricular",
                    "name": "Planificación y preparación previa de la enseñanza",
                    "score": None,
                    "max_score": 4,
                    "observable": False,
                    "summary": "No evaluable desde la grabación de una sola clase.",
                    "evidence": [],
                },
            ],
        },
        {
            "framework_id": "oecd_talis",
            "framework_name": "OECD/TALIS – Calidad de la enseñanza",
            "overall_score": 2.7,
            "dimensions": [
                {
                    "dimension_id": "classroom_management",
                    "name": "Gestión del aula y del tiempo",
                    "score": 3,
                    "max_score": 4,
                    "observable": True,
                    "summary": "Buen control general del flujo, con transiciones claras entre temas, aunque hay una digresión que consume tiempo de la sesión.",
                    "evidence": [
                        {"timestamp": 900.0, "quote": "Pasemos a la regla de la cadena, que sirve para derivar funciones compuestas, o sea una función dentro de otra función.", "comment": "Transición explícita y ordenada entre bloques."},
                    ],
                },
                {
                    "dimension_id": "supportive_climate",
                    "name": "Apoyo socioemocional y clima de apoyo",
                    "score": 3,
                    "max_score": 4,
                    "observable": True,
                    "summary": "Responde con paciencia a las dudas y genera un ambiente seguro para preguntar.",
                    "evidence": [
                        {"timestamp": 959.0, "quote": "Claro. Si tenemos seno de equis al cuadrado, la externa es el seno y la interna es equis al cuadrado, entonces queda coseno de equis al cuadrado por dos equis.", "comment": "Atiende la solicitud de ejemplo de un estudiante de forma completa."},
                    ],
                },
                {
                    "dimension_id": "cognitive_activation",
                    "name": "Activación cognitiva",
                    "score": 2,
                    "max_score": 4,
                    "observable": True,
                    "summary": "Las tareas y preguntas tienden a lo procedimental; falta conectar con conocimientos previos y plantear retos que exijan razonar más allá del cálculo mecánico.",
                    "evidence": [
                        {"timestamp": 240.0, "quote": "Ahora, ¿alguien me puede decir qué pasa con la derivada cuando la función es constante?", "comment": "Pregunta con potencial de razonamiento que no se llega a explotar."},
                    ],
                },
            ],
        },
    ],
    "strengths": [
        {"title": "Explicación estructurada con analogías", "detail": "Conecta la definición formal de derivada con la intuición física de la velocidad instantánea, facilitando la comprensión.", "timestamp": 20.0},
        {"title": "Refuerzo positivo a la participación", "detail": "Valida explícitamente las intervenciones correctas de los estudiantes, fortaleciendo el clima del aula.", "timestamp": 64.5},
    ],
    "improvements": [
        {"title": "Esperar la respuesta tras preguntar", "detail": "Lanza preguntas abiertas pero las responde él mismo, cerrando la oportunidad de razonamiento de los estudiantes.", "timestamp": 263.0, "suggestion": "Aplica la técnica de 'tiempo de espera': cuenta 5–7 segundos en silencio tras cada pregunta antes de dar la respuesta o de nominar a alguien."},
        {"title": "Reducir el monólogo docente", "detail": "El docente habla el 86% del tiempo. La participación estudiantil es baja y reactiva.", "timestamp": 240.0, "suggestion": "Inserta una pregunta dirigida a un estudiante específico tras cada bloque de explicación, o una micro-actividad en parejas."},
        {"title": "Acotar las digresiones", "detail": "Una anécdota personal se extiende y desvía la sesión de los objetivos.", "timestamp": 2040.0, "suggestion": "Usa anécdotas como gancho breve (máx. 30 s) y regresa de inmediato al contenido planificado."},
    ],
    "objective_alignment": {
        "aligned_pct": 0.85,
        "deviations": [
            {"start": 2040.0, "end": 2460.0, "note": "Digresión sobre una anécdota universitaria no relacionada con los objetivos de la sesión."},
        ],
    },
}


class FakeLLMProvider(LLMProvider):
    def complete(self, prompt: str) -> str:
        return json.dumps(_ANALYSIS, ensure_ascii=False)
