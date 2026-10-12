"""Evalua la ponderacion de guardrails contra la linea base del Sprint 11.

Reconsolida los niveles por guardrail versionados en
`validacion/resultados/resultados_guardrails.csv` con la rubrica actual, sin
volver a procesar los PDF del corpus. Asi se aisla el efecto de la
ponderacion de los cambios de señales lexicas.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from etica_ia_ers.dominio import (
    DefinicionGuardrail,
    DimensionEtica,
    EstadoAplicacionGuardrail,
    HallazgoEvaluacion,
    NivelCobertura,
    PrioridadDocumental,
    ResultadoAplicacionGuardrail,
    ResultadoDimensionEtica,
    ResultadoEvaluacionEtica,
)
from etica_ia_ers.modelo_etico_y_guardrails import GUARDRAILS_ACTIVOS
from etica_ia_ers.rubrica_y_agregacion import calculador


UMBRALES_SENSIBILIDAD = (0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def _escribir_csv(ruta: Path, filas: Iterable[dict], campos: list[str]) -> None:
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=campos,
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(filas)


def _evaluacion_documento(
    filas: list[dict[str, str]],
    catalogo: dict[str, DefinicionGuardrail],
) -> ResultadoEvaluacionEtica:
    analisis_id = uuid4()
    fecha = datetime.now(timezone.utc)
    aplicaciones = []
    for fila in filas:
        codigo = fila["guardrail"]
        if codigo not in catalogo:
            raise ValueError(f"El guardrail {codigo} no esta en el catalogo.")
        definicion = catalogo[codigo]
        hallazgo = HallazgoEvaluacion(
            analisis_id=analisis_id,
            guardrail_codigo=codigo,
            guardrail_version=definicion.version,
            familia_guardrail=definicion.familia,
            dimensiones_asociadas=(DimensionEtica(fila["dimension"]),),
            criterios_asociados=(),
            nivel_preliminar=NivelCobertura(fila["nivel_obtenido"]),
            prioridad_documental=PrioridadDocumental(fila["prioridad"]),
            justificacion=fila["justificacion"],
            justificacion_prioridad="Prioridad de la linea base.",
            requiere_revision_humana=False,
            motivo_revision_humana=None,
            evidencias=(),
            fecha_generacion=fecha,
            guardrail_nombre=fila["nombre_guardrail"],
            peso=definicion.peso_efectivo,
        )
        aplicaciones.append(
            ResultadoAplicacionGuardrail(
                guardrail_codigo=codigo,
                guardrail_version=definicion.version,
                estado=EstadoAplicacionGuardrail.APLICADO,
                motivo="Resultado de la linea base.",
                hallazgo=hallazgo,
            )
        )
    return ResultadoEvaluacionEtica(
        analisis_id=analisis_id,
        documento_id=uuid4(),
        fecha_inicio=fecha,
        fecha_fin=fecha,
        aplicaciones=tuple(aplicaciones),
    )


def _reconsolidar(
    por_documento: dict[str, list[dict[str, str]]],
    catalogo: dict[str, DefinicionGuardrail],
) -> dict[tuple[str, str], ResultadoDimensionEtica]:
    resultados = {}
    for documento, filas in por_documento.items():
        cobertura = calculador.calcular_cobertura_etica(
            _evaluacion_documento(filas, catalogo)
        )
        for resultado in cobertura.resultados_por_dimension:
            resultados[(documento, resultado.dimension.value)] = resultado
    return resultados


def _con_umbral(umbral: float, funcion, *argumentos):
    original = calculador.UMBRAL_EXPLICITO_PONDERADO
    calculador.UMBRAL_EXPLICITO_PONDERADO = umbral
    try:
        return funcion(*argumentos)
    finally:
        calculador.UMBRAL_EXPLICITO_PONDERADO = original


def _resumir(
    nombre: str,
    niveles: dict[tuple[str, str], str],
    referencias: dict[tuple[str, str], str],
) -> dict:
    acuerdo = sobreestimacion = subestimacion = 0
    for clave, esperado in referencias.items():
        obtenido = niveles[clave]
        acuerdo += obtenido == esperado
        sobreestimacion += (
            obtenido == "EXPLICITO" and esperado != "EXPLICITO"
        )
        subestimacion += obtenido == "PARCIAL" and esperado == "EXPLICITO"
    return {
        "regla": nombre,
        "casos": len(referencias),
        "aciertos_nivel": acuerdo,
        "acuerdo_nivel_pct": round(100 * acuerdo / len(referencias), 2),
        "explicito_sobreestimado": sobreestimacion,
        "explicito_subestimado": subestimacion,
    }


def ejecutar(resultados_base: Path, referencia: Path, salida: Path) -> None:
    filas_guardrails = _leer_csv(resultados_base / "resultados_guardrails.csv")
    filas_dimensiones = _leer_csv(resultados_base / "resultados_dimensiones.csv")
    referencias = {
        (fila["documento"], fila["dimension"]): fila["nivel_esperado"]
        for fila in _leer_csv(referencia)
    }
    linea_base = {
        (fila["documento"], fila["dimension"]): fila["nivel_obtenido"]
        for fila in filas_dimensiones
    }
    catalogo = {
        guardrail.definicion.codigo: guardrail.definicion
        for guardrail in GUARDRAILS_ACTIVOS
    }
    por_documento: dict[str, list[dict[str, str]]] = defaultdict(list)
    for fila in filas_guardrails:
        por_documento[fila["documento"]].append(fila)

    ponderados = _reconsolidar(por_documento, catalogo)
    salida.mkdir(parents=True, exist_ok=True)

    comparacion = []
    for clave in sorted(referencias):
        resultado = ponderados[clave]
        comparacion.append(
            {
                "documento": clave[0],
                "dimension": clave[1],
                "nivel_esperado": referencias[clave],
                "nivel_linea_base": linea_base[clave],
                "nivel_ponderado": resultado.nivel_consolidado.value,
                "cobertura_ponderada_pct": (
                    resultado.porcentaje_cobertura_ponderada
                ),
                "guardrails_criticos_pendientes": "; ".join(
                    resultado.guardrails_criticos_pendientes
                ),
                "cambio": str(
                    resultado.nivel_consolidado.value != linea_base[clave]
                ).upper(),
            }
        )
    _escribir_csv(
        salida / "comparacion_ponderacion.csv",
        comparacion,
        list(comparacion[0]),
    )

    resumen = [_resumir("LINEA_BASE", linea_base, referencias)]
    for umbral in UMBRALES_SENSIBILIDAD:
        resultados = _con_umbral(umbral, _reconsolidar, por_documento, catalogo)
        resumen.append(
            _resumir(
                f"PONDERADA_{umbral:.2f}",
                {
                    clave: resultado.nivel_consolidado.value
                    for clave, resultado in resultados.items()
                },
                referencias,
            )
        )
    _escribir_csv(
        salida / "resumen_ponderacion.csv",
        resumen,
        list(resumen[0]),
    )

    for fila in resumen:
        print(
            "{regla}: {aciertos_nivel}/{casos} ({acuerdo_nivel_pct:.2f}%), "
            "sobreestimados {explicito_sobreestimado}, "
            "subestimados {explicito_subestimado}".format(**fila)
        )


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resultados-base",
        type=Path,
        default=base / "resultados",
        help="Directorio con la corrida de referencia del Sprint 11.",
    )
    parser.add_argument(
        "--referencia",
        type=Path,
        default=base / "referencia_dimensiones.csv",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=base / "resultados_ponderacion",
    )
    argumentos = parser.parse_args()
    ejecutar(argumentos.resultados_base, argumentos.referencia, argumentos.salida)


if __name__ == "__main__":
    main()
