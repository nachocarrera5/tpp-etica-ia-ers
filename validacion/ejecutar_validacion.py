"""Ejecuta y documenta la validacion reproducible del Sprint 11."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from etica_ia_ers.api import ResultadoAnalisisResponse, _analizar_y_evaluar
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_ACTIVOS,
    RepositorioGuardrailsEnMemoria,
)


TAREAS_POR_DIMENSION = {
    "D01": "SCRUM-120",
    "D02": "SCRUM-120",
    "D03": "SCRUM-121",
    "D04": "SCRUM-121",
    "D05": "SCRUM-122",
    "D06": "SCRUM-122",
    "D07": "SCRUM-122",
    "D08": "SCRUM-123",
    "D09": "SCRUM-123",
    "D10": "SCRUM-123",
}


@dataclass(frozen=True)
class DocumentoCorpus:
    documento: str
    archivo: str
    tipo: str
    origen: str
    dominio: str


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


def _commit_actual() -> str:
    proceso = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return proceso.stdout.strip() or "DESCONOCIDO"


def _catalogo_por_codigo() -> dict[str, object]:
    return {
        guardrail.definicion.codigo: guardrail.definicion
        for guardrail in GUARDRAILS_ACTIVOS
    }


def ejecutar(
    corpus_dir: Path,
    salida: Path,
    referencia: Path | None,
) -> None:
    base = Path(__file__).resolve().parent
    documentos = [
        DocumentoCorpus(**fila) for fila in _leer_csv(base / "corpus.csv")
    ]
    referencias = (
        {
            (fila["documento"], fila["dimension"]): fila
            for fila in _leer_csv(referencia)
        }
        if referencia is not None
        else {}
    )
    catalogo = _catalogo_por_codigo()
    repositorio = RepositorioGuardrailsEnMemoria(GUARDRAILS_ACTIVOS)
    salida.mkdir(parents=True, exist_ok=True)

    filas_guardrails: list[dict] = []
    filas_dimensiones: list[dict] = []
    evidencias: list[dict] = []

    for item in documentos:
        ruta_documento = corpus_dir / item.archivo
        if not ruta_documento.is_file():
            raise FileNotFoundError(f"No se encontro {ruta_documento}")

        documento = cargar_documento_desde_ruta(
            ruta_documento,
            metadatos={
                "identificador_ers": item.documento,
                "dominio": item.dominio,
                "origen_validacion": item.origen,
                "tipo_corpus": item.tipo,
            },
        )
        resultado = ResultadoAnalisisResponse.model_validate(
            _analizar_y_evaluar(documento, repositorio)
        )

        for hallazgo in resultado.hallazgos:
            definicion = catalogo[hallazgo.guardrail_codigo]
            dimension = definicion.dimensiones[0].value
            filas_guardrails.append(
                {
                    "documento": item.documento,
                    "tipo_documento": item.tipo,
                    "tarea": TAREAS_POR_DIMENSION[dimension],
                    "dimension": dimension,
                    "guardrail": hallazgo.guardrail_codigo,
                    "nombre_guardrail": hallazgo.guardrail_nombre or "",
                    "nivel_obtenido": hallazgo.nivel_preliminar.value,
                    "prioridad": hallazgo.prioridad_documental.value,
                    "cantidad_evidencias": len(hallazgo.evidencias),
                    "justificacion": hallazgo.justificacion,
                }
            )
            for evidencia in hallazgo.evidencias:
                evidencias.append(
                    {
                        "documento": item.documento,
                        "dimension": dimension,
                        "guardrail": hallazgo.guardrail_codigo,
                        "nivel": hallazgo.nivel_preliminar.value,
                        "fragmento_id": str(evidencia.fragmento_id),
                        "seccion": evidencia.seccion_origen,
                        "texto": evidencia.texto,
                        "fragmentos_clave": list(evidencia.fragmentos_clave),
                        "observacion": evidencia.observacion,
                    }
                )

        for dimension in resultado.resultados_dimension:
            codigo = dimension.dimension_codigo.value
            filas_dimensiones.append(
                {
                    "documento": item.documento,
                    "tipo_documento": item.tipo,
                    "tarea": TAREAS_POR_DIMENSION[codigo],
                    "dimension": codigo,
                    "nivel_obtenido": (
                        dimension.nivel_consolidado.value
                        if dimension.nivel_consolidado
                        else "NO_EVALUADA"
                    ),
                    "prioridad": (
                        dimension.prioridad_documental.value
                        if dimension.prioridad_documental
                        else ""
                    ),
                    "cantidad_hallazgos": len(dimension.hallazgos_relacionados),
                    "cantidad_brechas": len(dimension.brechas_principales),
                }
            )

    _escribir_csv(
        salida / "resultados_guardrails.csv",
        filas_guardrails,
        list(filas_guardrails[0]),
    )
    _escribir_csv(
        salida / "resultados_dimensiones.csv",
        filas_dimensiones,
        list(filas_dimensiones[0]),
    )
    if referencias:
        comparacion = _comparar(filas_dimensiones, referencias)
        metricas = _calcular_metricas(comparacion)
        _escribir_csv(
            salida / "comparacion_referencia.csv",
            comparacion,
            list(comparacion[0]),
        )
        _escribir_csv(
            salida / "resumen_metricas.csv",
            metricas,
            list(metricas[0]),
        )
        (salida / "informe.md").write_text(
            _crear_informe(metricas, comparacion), encoding="utf-8"
        )
    (salida / "evidencias.json").write_text(
        json.dumps(evidencias, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (salida / "manifiesto.json").write_text(
        json.dumps(
            {
                "fecha_utc": datetime.now(timezone.utc).isoformat(),
                "commit": _commit_actual(),
                "documentos": [asdict(item) for item in documentos],
                "cantidad_guardrails": len(GUARDRAILS_ACTIVOS),
                "cantidad_evaluaciones": len(filas_guardrails),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _comparar(
    obtenidos: list[dict], referencias: dict[tuple[str, str], dict[str, str]]
) -> list[dict]:
    filas = []
    for obtenido in obtenidos:
        clave = (obtenido["documento"], obtenido["dimension"])
        if clave not in referencias:
            raise ValueError(f"Falta referencia para {clave[0]} {clave[1]}")
        referencia = referencias[clave]
        esperado = referencia["nivel_esperado"]
        real = obtenido["nivel_obtenido"]
        esperado_presente = esperado != "AUSENTE"
        real_presente = real not in {"AUSENTE", "NO_EVALUADA"}
        filas.append(
            {
                **obtenido,
                "nivel_esperado": esperado,
                "acuerdo_nivel": str(real == esperado).upper(),
                "evidencia_esperada": str(esperado_presente).upper(),
                "evidencia_obtenida": str(real_presente).upper(),
                "resultado_deteccion": _resultado_deteccion(
                    esperado_presente, real_presente
                ),
                "justificacion_referencia": referencia["justificacion"],
                "estado_revision": referencia["estado_revision"],
            }
        )
    return filas


def _resultado_deteccion(esperado: bool, real: bool) -> str:
    if esperado and real:
        return "VP"
    if esperado:
        return "FN"
    if real:
        return "FP"
    return "VN"


def _calcular_metricas(comparacion: list[dict]) -> list[dict]:
    grupos: dict[str, list[dict]] = defaultdict(list)
    for fila in comparacion:
        grupos[fila["tarea"]].append(fila)
    grupos["TOTAL"] = comparacion

    metricas = []
    for tarea, filas in grupos.items():
        conteos = {
            clave: sum(fila["resultado_deteccion"] == clave for fila in filas)
            for clave in ("VP", "VN", "FP", "FN")
        }
        precision = _division(conteos["VP"], conteos["VP"] + conteos["FP"])
        exhaustividad = _division(
            conteos["VP"], conteos["VP"] + conteos["FN"]
        )
        f1 = _division(2 * precision * exhaustividad, precision + exhaustividad)
        metricas.append(
            {
                "tarea": tarea,
                "casos": len(filas),
                "aciertos_nivel": sum(
                    fila["acuerdo_nivel"] == "TRUE" for fila in filas
                ),
                "acuerdo_nivel_pct": round(
                    100
                    * sum(fila["acuerdo_nivel"] == "TRUE" for fila in filas)
                    / len(filas),
                    2,
                ),
                **conteos,
                "precision_pct": round(100 * precision, 2),
                "exhaustividad_pct": round(100 * exhaustividad, 2),
                "f1_pct": round(100 * f1, 2),
            }
        )
    return metricas


def _division(numerador: float, denominador: float) -> float:
    return numerador / denominador if denominador else 0.0


def _crear_informe(metricas: list[dict], comparacion: list[dict]) -> str:
    lineas = [
        "# Informe de validacion del Sprint 11",
        "",
        "Resultados preliminares sujetos a una segunda revision humana.",
        "",
        "| Tarea | Casos | Acuerdo de nivel | Precision | Exhaustividad | F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for metrica in metricas:
        lineas.append(
            "| {tarea} | {casos} | {acuerdo_nivel_pct:.2f}% | "
            "{precision_pct:.2f}% | {exhaustividad_pct:.2f}% | {f1_pct:.2f}% |".format(
                **metrica
            )
        )

    lineas.extend(["", "## Diferencias", ""])
    diferencias = [
        fila
        for fila in comparacion
        if fila["acuerdo_nivel"] != "TRUE"
    ]
    if not diferencias:
        lineas.append("No se registraron diferencias contra la referencia.")
    else:
        lineas.extend(
            [
                "| Documento | Dimension | Esperado | Obtenido | Tipo |",
                "|---|---|---|---|---|",
            ]
        )
        for fila in diferencias:
            lineas.append(
                "| {documento} | {dimension} | {nivel_esperado} | "
                "{nivel_obtenido} | {resultado_deteccion} |".format(**fila)
            )

    lineas.extend(
        [
            "",
            "## Interpretacion",
            "",
            "La precision y la exhaustividad miden deteccion de evidencia, no "
            "cumplimiento etico. El acuerdo de nivel exige ademas coincidir en "
            "la graduacion AUSENTE/PARCIAL/EXPLICITO. Las diferencias deben "
            "revisarse sobre las evidencias JSON antes de ajustar el catalogo.",
            "",
        ]
    )
    return "\n".join(lineas)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument(
        "--referencia",
        type=Path,
        default=None,
        help=(
            "CSV de referencia. Si se omite, solo se registran los resultados "
            "del motor."
        ),
    )
    argumentos = parser.parse_args()
    ejecutar(argumentos.corpus, argumentos.salida, argumentos.referencia)


if __name__ == "__main__":
    main()
