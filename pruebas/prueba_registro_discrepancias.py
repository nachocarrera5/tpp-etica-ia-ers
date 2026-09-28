import csv
from pathlib import Path


DIRECTORIO_VALIDACION = Path(__file__).resolve().parents[1] / "validacion"


def _leer_csv(nombre: str) -> list[dict[str, str]]:
    with (DIRECTORIO_VALIDACION / nombre).open(
        encoding="utf-8", newline=""
    ) as archivo:
        return list(csv.DictReader(archivo))


def prueba_registro_incluye_todos_los_falsos_positivos_y_negativos():
    comparacion = _leer_csv("resultados/comparacion_referencia.csv")
    registro = _leer_csv("registro_discrepancias.csv")

    esperados = {
        (fila["resultado_deteccion"], fila["documento"], fila["dimension"])
        for fila in comparacion
        if fila["resultado_deteccion"] in {"FP", "FN"}
    }
    registrados = {
        (
            "FP" if fila["tipo"] == "FALSO_POSITIVO" else "FN",
            fila["documento"],
            fila["dimension"],
        )
        for fila in registro
        if fila["tipo"] in {"FALSO_POSITIVO", "FALSO_NEGATIVO"}
    }

    assert registrados == esperados
    assert len(esperados) == 3


def prueba_subestimacion_registra_todos_los_desacuerdos_de_nivel():
    comparacion = _leer_csv("resultados/comparacion_referencia.csv")
    registro = _leer_csv("registro_discrepancias.csv")

    cantidad_esperada = sum(
        fila["acuerdo_nivel"] == "FALSE"
        and fila["resultado_deteccion"] == "VP"
        for fila in comparacion
    )
    calibracion = [
        fila for fila in registro if fila["tipo"] == "SUBESTIMACION_NIVEL"
    ]

    assert len(calibracion) == 1
    assert int(calibracion[0]["cantidad_casos"]) == cantidad_esperada == 29


def prueba_entradas_tienen_trazabilidad_y_accion_posterior():
    registro = _leer_csv("registro_discrepancias.csv")

    assert len({fila["id"] for fila in registro}) == len(registro)
    assert all(fila["causa_probable"].strip() for fila in registro)
    assert all(fila["correccion_propuesta"].strip() for fila in registro)
    assert all(fila["tarea_destino"].strip() for fila in registro)
    assert all(
        fila["estado"] == "CONFIRMADO_PRIMERA_REVISION" for fila in registro
    )
