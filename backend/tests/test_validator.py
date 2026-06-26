"""
Tests del validador anti-alucinación. ESTO es la validación del producto: una
cita que no existe literalmente en la transcripción se descarta. La confianza de
la herramienta depende de que esto funcione.
"""
from app.analysis.validator import validate_analysis

TRANSCRIPT = {
    "segments": [
        {"speaker": "teacher", "start": 20.0, "end": 41.2, "text": "La derivada mide la razón de cambio instantánea de una función."},
        {"speaker": "teacher", "start": 64.5, "end": 78.0, "text": "Exacto, muy buena observación."},
    ]
}


def _analysis_con_quote(quote: str, timestamp=20.0) -> dict:
    return {
        "frameworks": [
            {
                "framework_id": "x",
                "dimensions": [
                    {"dimension_id": "d", "evidence": [{"timestamp": timestamp, "quote": quote}]}
                ],
            }
        ]
    }


def test_cita_exacta_se_conserva():
    a = _analysis_con_quote("La derivada mide la razón de cambio instantánea de una función.")
    cleaned, report = validate_analysis(a, TRANSCRIPT)
    assert report["valid"] == 1 and report["invalid"] == 0
    assert len(cleaned["frameworks"][0]["dimensions"][0]["evidence"]) == 1


def test_cita_inventada_se_descarta():
    a = _analysis_con_quote("Esto nunca lo dijo el profesor en clase.")
    cleaned, report = validate_analysis(a, TRANSCRIPT)
    assert report["invalid"] == 1 and report["valid"] == 0
    assert cleaned["frameworks"][0]["dimensions"][0]["evidence"] == []


def test_normalizacion_tolera_tildes_y_mayusculas():
    # misma frase sin tildes y en mayúsculas: debe seguir anclando
    a = _analysis_con_quote("LA DERIVADA MIDE LA RAZON DE CAMBIO INSTANTANEA DE UNA FUNCION.")
    _, report = validate_analysis(a, TRANSCRIPT)
    assert report["valid"] == 1


def test_timestamp_muy_lejos_invalida_la_cita():
    # cita correcta pero timestamp absurdo (fuera de tolerancia) -> descartada
    a = _analysis_con_quote(
        "La derivada mide la razón de cambio instantánea de una función.",
        timestamp=9999.0,
    )
    _, report = validate_analysis(a, TRANSCRIPT)
    assert report["invalid"] == 1


def test_analisis_vacio_no_revienta():
    cleaned, report = validate_analysis({}, TRANSCRIPT)
    assert report["total"] == 0
    assert cleaned["frameworks"] == []
