"""
Tests de las métricas duras (funciones PURAS, cero LLM). Son la columna vertebral
factual del análisis: si esto está bien, el LLM no puede alucinar los números.
"""
from app.metrics import pace, questions, talk_ratio
from app.metrics.runner import compute_all_metrics


# --- transcript de juguete, fácil de razonar a mano ----------------------- #
SEGMENTS = [
    {"speaker": "teacher", "start": 0.0, "end": 30.0, "text": "Hola, hoy vemos derivadas. ¿Entienden la idea?"},
    {"speaker": "student", "start": 31.0, "end": 35.0, "text": "Sí profe, más o menos."},
    {"speaker": "teacher", "start": 50.0, "end": 80.0, "text": "Bueno, o sea, la derivada es la pendiente. ¿Alguna duda?"},
    {"speaker": "student", "start": 81.0, "end": 84.0, "text": "No, ninguna."},
]


def test_talk_ratio_suma_uno_y_favorece_al_docente():
    teacher, students = talk_ratio.talk_ratio(SEGMENTS)
    # docente: 30 + 30 = 60 s; estudiantes: 4 + 3 = 7 s -> 60/67
    assert teacher == 0.90
    assert students == 0.10
    assert round(teacher + students, 2) == 1.0


def test_talk_ratio_vacio_no_revienta():
    assert talk_ratio.talk_ratio([]) == (0.0, 0.0)


def test_total_questions_solo_cuenta_turnos_del_docente():
    # 2 signos '?' en turnos del docente; los del estudiante no cuentan
    assert questions.total_questions(SEGMENTS) == 2


def test_student_interventions_cuenta_turnos_no_docente():
    assert questions.student_interventions(SEGMENTS) == 2


def test_words_per_minute_usa_solo_tiempo_del_docente():
    wpm = pace.words_per_minute(SEGMENTS)
    # el docente habla 60 s (1 min); el WPM debe ser > 0 y razonable
    assert wpm > 0
    # ~13 palabras del docente en 1 min -> alrededor de 13
    assert 5 <= wpm <= 40


def test_long_silences_detecta_gap_mayor_al_umbral():
    # gap docente->docente entre 35.0 y 50.0 = 15 s > 8
    sil = pace.long_silences(SEGMENTS, threshold=8.0)
    assert len(sil) == 1
    assert sil[0]["start"] == 35.0
    assert sil[0]["end"] == 50.0


def test_long_silences_umbral_alto_no_detecta_nada():
    assert pace.long_silences(SEGMENTS, threshold=60.0) == []


def test_filler_words_cuenta_muletillas_del_docente():
    res = pace.filler_words(SEGMENTS, ["o sea", "bueno", "este"], top_n=5)
    assert res["count"] == 2  # "bueno" x1 + "o sea" x1
    palabras = {item["word"] for item in res["top"]}
    assert "bueno" in palabras
    assert "o sea" in palabras


def test_compute_all_metrics_arma_el_contrato_completo():
    m = compute_all_metrics({"segments": SEGMENTS})
    for key in (
        "talk_ratio_teacher",
        "talk_ratio_students",
        "words_per_minute",
        "total_questions",
        "student_interventions",
        "long_silences",
        "filler_words",
        "visual_timeline",
    ):
        assert key in m
    assert m["visual_timeline"] == []  # sin video en el MVP
    assert m["filler_words"]["count"] >= 0
