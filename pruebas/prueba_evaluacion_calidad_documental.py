import csv
import json
from pathlib import Path

from validacion.evaluar_calidad_documental import (
    _evaluar_cobertura,
    _evaluar_evidencia,
    _evaluar_verificabilidad,
    _porcentaje,
)


DIRECTORIO_VALIDACION = Path(__file__).resolve().parents[1] / "validacion"


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def prueba_porcentaje_resuelve_cero_y_redondea():
    assert _porcentaje(1, 3) == 33.33
    assert _porcentaje(0, 0) == 0.0


def prueba_cobertura_separa_ausente_parcial_y_explicito():
    corpus = [
        {
            "documento": "ERS-1",
            "tipo": "SINTETICA",
        }
    ]
    dimensiones = [
        {"documento": "ERS-1", "nivel_obtenido": nivel}
        for nivel in ("AUSENTE", "PARCIAL", "EXPLICITO")
    ]

    [resultado] = _evaluar_cobertura(corpus, dimensiones)

    assert resultado["dimensiones_evaluadas"] == 3
    assert resultado["ausentes"] == 1
    assert resultado["parciales"] == 1
    assert resultado["explicitas"] == 1
    assert resultado["cobertura_no_ausente_pct"] == 66.67


def prueba_verificabilidad_filtra_solo_familia_verif():
    corpus = [{"documento": "ERS-1", "tipo": "REAL"}]
    guardrails = [
        {
            "documento": "ERS-1",
            "guardrail": "GR-D01-VERIF-SUPUESTOS",
            "nivel_obtenido": "PARCIAL",
        },
        {
            "documento": "ERS-1",
            "guardrail": "GR-D01-PRES-PROPOSITO",
            "nivel_obtenido": "EXPLICITO",
        },
    ]

    [resultado] = _evaluar_verificabilidad(corpus, guardrails)

    assert resultado["guardrails_verificabilidad"] == 1
    assert resultado["con_evidencia"] == 1
    assert resultado["con_evidencia_pct"] == 100.0


def prueba_evidencia_detecta_inconsistencia_entre_nivel_y_vinculos():
    corpus = [{"documento": "ERS-1", "tipo": "REAL"}]
    guardrails = [
        {
            "documento": "ERS-1",
            "nivel_obtenido": "AUSENTE",
            "cantidad_evidencias": "1",
        },
        {
            "documento": "ERS-1",
            "nivel_obtenido": "PARCIAL",
            "cantidad_evidencias": "0",
        },
    ]

    [resultado] = _evaluar_evidencia(corpus, guardrails)

    assert resultado["inconsistencias_nivel_evidencia"] == 2


def prueba_resultados_publicados_conservan_la_linea_base():
    directorio = DIRECTORIO_VALIDACION / "resultados_calidad"
    resumen = json.loads(
        (directorio / "resumen_calidad_documental.json").read_text(
            encoding="utf-8"
        )
    )

    assert resumen["corpus"] == {
        "documentos": 7,
        "dimensiones": 70,
        "aplicaciones_guardrail": 504,
    }
    assert resumen["cobertura_etica"]["cobertura_no_ausente_pct"] == 90.0
    assert resumen["ambiguedad"]["total_senales"] == 154
    assert resumen["ambiguedad"]["palabras_normalizadas"] == 83705
    assert resumen["ambiguedad"]["senales_cada_1000_palabras"] == 1.84
    assert resumen["verificabilidad"]["con_evidencia"] == 57
    assert resumen["evidencia_documental"][
        "inconsistencias_nivel_evidencia"
    ] == 0
    assert len(_leer_csv(directorio / "cobertura_por_documento.csv")) == 7
    hashes = _leer_csv(directorio / "hashes_corpus.csv")
    assert len(hashes) == 7
    assert all(len(fila["sha256"]) == 64 for fila in hashes)
