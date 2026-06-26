"""
OECD/TALIS — Calidad de la enseñanza. Tres dominios observables del marco TALIS.
Las dimensiones son DATOS, descritas con palabras propias.
"""
from __future__ import annotations

FRAMEWORK = {
    "framework_id": "oecd_talis",
    "framework_name": "OECD/TALIS – Calidad de la enseñanza",
    "dimensions": [
        {
            "dimension_id": "classroom_management",
            "name": "Gestión del aula y del tiempo",
            "description": "Organización del aula y del tiempo para maximizar el tiempo de aprendizaje.",
            "look_for": "Transiciones ordenadas, claridad de instrucciones, control del flujo, mínima pérdida de tiempo.",
            "observable_from_recording": True,
        },
        {
            "dimension_id": "supportive_climate",
            "name": "Apoyo socioemocional y clima de apoyo",
            "description": "Relaciones de apoyo entre docente y estudiantes que generan seguridad para participar.",
            "look_for": "Paciencia ante dudas, retroalimentación respetuosa, ambiente seguro para preguntar y equivocarse.",
            "observable_from_recording": True,
        },
        {
            "dimension_id": "cognitive_activation",
            "name": "Activación cognitiva",
            "description": "Tareas y preguntas que exigen razonamiento profundo y conexión de ideas.",
            "look_for": "Problemas que admiten varias estrategias, preguntas que exigen justificar, conexión con conocimientos previos.",
            "observable_from_recording": True,
        },
    ],
}
