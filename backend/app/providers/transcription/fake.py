"""
Proveedor de transcripción FAKE. Ignora el audio y devuelve EXACTAMENTE los
segmentos del mock canónico (`frontend/src/mocks/sample_session.json`, clase de
Cálculo I). Esto permite correr el pipeline end-to-end SIN ninguna API key.

Si tocas estos segmentos, rompes la paridad con el mock del frontend.
"""
from __future__ import annotations

from .base import TranscriptionProvider

# Copia textual de transcript.segments del mock canónico. NO editar sin
# sincronizar con frontend/src/mocks/sample_session.json.
_SEGMENTS = [
    {"speaker": "teacher", "start": 8.0, "end": 19.4, "text": "Buenos días a todos. Hoy vamos a estudiar uno de los conceptos más importantes del curso: la derivada."},
    {"speaker": "teacher", "start": 20.0, "end": 41.2, "text": "La derivada mide la razón de cambio instantánea de una función. Piensen en la velocidad de un auto en un instante exacto, no en el promedio del viaje."},
    {"speaker": "teacher", "start": 42.0, "end": 58.6, "text": "Formalmente la definimos como el límite del cociente incremental cuando el incremento de equis tiende a cero."},
    {"speaker": "student", "start": 60.1, "end": 64.0, "text": "Profe, ¿eso es lo mismo que la pendiente de la recta tangente?"},
    {"speaker": "teacher", "start": 64.5, "end": 78.0, "text": "Exacto, muy buena observación. La derivada en un punto es precisamente la pendiente de la recta tangente a la curva en ese punto."},
    {"speaker": "teacher", "start": 240.0, "end": 262.5, "text": "Ahora, ¿alguien me puede decir qué pasa con la derivada cuando la función es constante?"},
    {"speaker": "teacher", "start": 263.0, "end": 271.0, "text": "Bueno, sigamos, la derivada de una constante es cero porque no hay cambio."},
    {"speaker": "teacher", "start": 900.0, "end": 922.0, "text": "Pasemos a la regla de la cadena, que sirve para derivar funciones compuestas, o sea una función dentro de otra función."},
    {"speaker": "teacher", "start": 923.0, "end": 951.0, "text": "La idea es derivar la función externa dejando la interna intacta, y luego multiplicar por la derivada de la función interna."},
    {"speaker": "student", "start": 952.0, "end": 958.4, "text": "¿Puede poner un ejemplo con seno de equis al cuadrado?"},
    {"speaker": "teacher", "start": 959.0, "end": 985.0, "text": "Claro. Si tenemos seno de equis al cuadrado, la externa es el seno y la interna es equis al cuadrado, entonces queda coseno de equis al cuadrado por dos equis."},
    {"speaker": "student", "start": 986.0, "end": 990.2, "text": "Ah, ya entendí, primero la de afuera y después multiplico."},
    {"speaker": "teacher", "start": 1394.0, "end": 1410.0, "text": "¿Todos de acuerdo hasta aquí? Perfecto, avancemos entonces con un ejercicio más difícil."},
    {"speaker": "teacher", "start": 2040.0, "end": 2068.0, "text": "Esto me recuerda una anécdota de cuando yo estudiaba en la universidad, había un profesor muy estricto que nos hacía exámenes durísimos."},
    {"speaker": "teacher", "start": 2460.0, "end": 2483.0, "text": "Bueno, volviendo al tema, practiquen en casa la regla de la cadena con al menos diez ejercicios del libro."},
    {"speaker": "student", "start": 2484.0, "end": 2488.0, "text": "Profe, ¿esto entra en el examen del viernes?"},
    {"speaker": "teacher", "start": 2489.0, "end": 2503.0, "text": "Sí, entra todo lo de hoy. Repasen bien la definición y la regla de la cadena, son fundamentales."},
]


class FakeTranscriptionProvider(TranscriptionProvider):
    def transcribe(self, audio_path: str) -> dict:
        # Devuelve copias para que nadie mute la constante del módulo.
        return {"segments": [dict(s) for s in _SEGMENTS]}
