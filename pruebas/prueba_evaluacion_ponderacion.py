from pathlib import Path

from validacion.evaluar_ponderacion import _leer_csv, ejecutar


DIRECTORIO_VALIDACION = Path(__file__).resolve().parents[1] / "validacion"


def prueba_ponderacion_mejora_la_linea_base_sin_sobreestimar(tmp_path):
    ejecutar(
        DIRECTORIO_VALIDACION / "resultados",
        DIRECTORIO_VALIDACION / "referencia_dimensiones.csv",
        tmp_path,
    )

    resumen = {
        fila["regla"]: fila
        for fila in _leer_csv(tmp_path / "resumen_ponderacion.csv")
    }
    linea_base = resumen["LINEA_BASE"]
    ponderada = resumen["PONDERADA_0.85"]
    assert int(ponderada["aciertos_nivel"]) >= int(linea_base["aciertos_nivel"])
    assert ponderada["explicito_sobreestimado"] == "0"


def prueba_ponderacion_solo_eleva_dimensiones_sin_criticos_pendientes(tmp_path):
    ejecutar(
        DIRECTORIO_VALIDACION / "resultados",
        DIRECTORIO_VALIDACION / "referencia_dimensiones.csv",
        tmp_path,
    )

    for fila in _leer_csv(tmp_path / "comparacion_ponderacion.csv"):
        if fila["nivel_ponderado"] != "EXPLICITO":
            continue
        assert fila["guardrails_criticos_pendientes"] == ""
        assert float(fila["cobertura_ponderada_pct"]) >= 85.0
