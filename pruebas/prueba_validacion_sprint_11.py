from pathlib import Path

from validacion.ejecutar_validacion import (
    _calcular_metricas,
    _comparar,
    _leer_csv,
    _resultado_deteccion,
)


DIRECTORIO_VALIDACION = Path(__file__).resolve().parents[1] / "validacion"


def prueba_resultado_deteccion_distingue_los_cuatro_casos():
    assert _resultado_deteccion(True, True) == "VP"
    assert _resultado_deteccion(False, False) == "VN"
    assert _resultado_deteccion(False, True) == "FP"
    assert _resultado_deteccion(True, False) == "FN"


def prueba_comparacion_separa_nivel_y_presencia_de_evidencia():
    obtenidos = [
        {
            "documento": "ERS-1",
            "tipo_documento": "SINTETICA",
            "tarea": "SCRUM-120",
            "dimension": "D01",
            "nivel_obtenido": "PARCIAL",
            "prioridad": "ALTA",
            "cantidad_hallazgos": 7,
            "cantidad_brechas": 2,
        }
    ]
    referencias = {
        ("ERS-1", "D01"): {
            "nivel_esperado": "EXPLICITO",
            "justificacion": "La ERS cubre los criterios.",
            "estado_revision": "REVISADA",
        }
    }

    fila = _comparar(obtenidos, referencias)[0]

    assert fila["acuerdo_nivel"] == "FALSE"
    assert fila["resultado_deteccion"] == "VP"


def prueba_metricas_calculan_precision_exhaustividad_y_f1():
    comparacion = [
        {
            "tarea": "SCRUM-121",
            "acuerdo_nivel": "TRUE",
            "resultado_deteccion": resultado,
        }
        for resultado in ("VP", "VP", "VN", "FP", "FN")
    ]

    metrica = _calcular_metricas(comparacion)[0]

    assert metrica["casos"] == 5
    assert metrica["precision_pct"] == 66.67
    assert metrica["exhaustividad_pct"] == 66.67
    assert metrica["f1_pct"] == 66.67


def prueba_referencia_cubre_diez_dimensiones_de_los_siete_documentos():
    corpus = _leer_csv(DIRECTORIO_VALIDACION / "corpus.csv")
    referencias = _leer_csv(
        DIRECTORIO_VALIDACION / "referencia_dimensiones.csv"
    )
    documentos = {fila["documento"] for fila in corpus}

    assert len(documentos) == 7
    assert len(referencias) == 70
    assert {fila["documento"] for fila in referencias} == documentos
    for documento in documentos:
        dimensiones = {
            fila["dimension"]
            for fila in referencias
            if fila["documento"] == documento
        }
        assert dimensiones == {f"D{numero:02}" for numero in range(1, 11)}


def prueba_resultados_publicados_coinciden_con_la_referencia_actual():
    obtenidos = _leer_csv(
        DIRECTORIO_VALIDACION / "resultados" / "resultados_dimensiones.csv"
    )
    referencias = {
        (fila["documento"], fila["dimension"]): fila
        for fila in _leer_csv(
            DIRECTORIO_VALIDACION / "referencia_dimensiones.csv"
        )
    }

    total = _calcular_metricas(_comparar(obtenidos, referencias))[-1]

    assert total["casos"] == 70
    assert total["VP"] == 62
    assert total["VN"] == 5
    assert total["FP"] == 1
    assert total["FN"] == 2
    assert total["f1_pct"] == 97.64
