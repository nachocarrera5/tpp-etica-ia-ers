"""Exportacion del reporte de cobertura etica documental (SCRUM-112).

Ejecuta la cadena completa sobre cada ERS de `ejemplos/ers/` (o sobre las rutas
pasadas como argumento) y guarda el reporte en `datos/salida/`, en los formatos
JSON, Markdown y HTML.

    entrada -> NLP -> motor de evaluacion -> rubrica -> reporte -> exportacion

Uso desde la raiz del proyecto:

    python3 -m pip install -e .
    python3 ejemplos/exportar_reporte.py
    python3 ejemplos/exportar_reporte.py ruta/a/otra_ers.txt --formato md
    python3 ejemplos/exportar_reporte.py --salida /tmp/reportes
"""

import argparse
from pathlib import Path
from typing import List, Sequence

from etica_ia_ers.dominio import SolicitudEvaluacionEtica
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_ACTIVOS,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto
from etica_ia_ers.resultados_y_presentacion import (
    DIRECTORIO_SALIDA,
    FormatoExportacion,
    escribir_reporte,
    exportar_reporte_documento,
    formatos_disponibles,
)

DIRECTORIO_ERS = Path(__file__).resolve().parent / "ers"


def _rutas_a_exportar(argumentos: Sequence[str]) -> List[Path]:
    if argumentos:
        return [Path(argumento) for argumento in argumentos]
    return sorted(DIRECTORIO_ERS.glob("*.txt"))


def _formatos_pedidos(formatos: Sequence[str]) -> List[FormatoExportacion]:
    if not formatos:
        return list(FormatoExportacion)
    # Se conserva el orden pedido sin repetir un mismo formato.
    elegidos: List[FormatoExportacion] = []
    for formato in formatos:
        resuelto = FormatoExportacion.desde_texto(formato)
        if resuelto not in elegidos:
            elegidos.append(resuelto)
    return elegidos


def _exportar(
    ruta: Path,
    formatos: Sequence[FormatoExportacion],
    directorio_salida: Path,
) -> None:
    documento = cargar_documento_desde_ruta(ruta)
    resultado_nlp = analizar_texto(documento.contenido_extraido)
    motor = MotorEvaluacionEtica(RepositorioGuardrailsEnMemoria(GUARDRAILS_ACTIVOS))
    evaluacion = motor.evaluar(
        SolicitudEvaluacionEtica(
            documento_id=documento.id,
            resultado_nlp=resultado_nlp,
            metadatos=documento.metadatos,
        )
    )

    print(f"ERS: {ruta.name}  ({len(evaluacion.hallazgos)} hallazgos)")
    for formato in formatos:
        reporte = exportar_reporte_documento(
            evaluacion,
            nombre_documento=documento.nombre_original,
            formato=formato,
        )
        destino = escribir_reporte(reporte, directorio_salida)
        print(f"  {formato.value:<8} -> {destino}")


def main(argumentos: Sequence[str]) -> None:
    analizador = argparse.ArgumentParser(
        description="Exporta el reporte de cobertura etica documental de una ERS."
    )
    analizador.add_argument(
        "rutas",
        nargs="*",
        help="ERS a analizar. Sin argumentos usa las ERS de ejemplo.",
    )
    analizador.add_argument(
        "--formato",
        action="append",
        default=[],
        metavar="FORMATO",
        help=(
            "Formato a exportar; puede repetirse. Valores aceptados: "
            + ", ".join(formatos_disponibles())
            + ". Por defecto exporta todos."
        ),
    )
    analizador.add_argument(
        "--salida",
        default=str(DIRECTORIO_SALIDA),
        metavar="DIRECTORIO",
        help=f"Directorio donde escribir los reportes (por defecto {DIRECTORIO_SALIDA}).",
    )
    opciones = analizador.parse_args(list(argumentos))

    rutas = _rutas_a_exportar(opciones.rutas)
    if not rutas:
        print(f"No se encontraron ERS para exportar en {DIRECTORIO_ERS}.")
        return

    formatos = _formatos_pedidos(opciones.formato)
    directorio_salida = Path(opciones.salida)
    for ruta in rutas:
        _exportar(ruta, formatos, directorio_salida)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
