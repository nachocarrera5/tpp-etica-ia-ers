"""Demostracion del pipeline NLP sobre ERS de ejemplo (SCRUM-103).

Carga cada ERS de `ejemplos/ers/` (o las rutas pasadas como argumento), ejecuta
el pipeline NLP completo e imprime un reporte legible con clasificaciones y
senales extraidas. No escribe resultados en disco.

Uso desde la raiz del proyecto:

    python3 -m pip install -e .
    python3 ejemplos/analizar_ers.py
    python3 ejemplos/analizar_ers.py ruta/a/otra_ers.txt
"""

from collections import Counter
from pathlib import Path
from typing import List, Sequence

from etica_ia_ers.dominio import ResultadoAnalisisNLP
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto

DIRECTORIO_ERS = Path(__file__).resolve().parent / "ers"


def _rutas_a_analizar(argumentos: Sequence[str]) -> List[Path]:
    if argumentos:
        return [Path(argumento) for argumento in argumentos]
    return sorted(DIRECTORIO_ERS.glob("*.txt"))


def _truncar(texto: str, largo: int = 60) -> str:
    una_linea = " ".join(texto.split())
    if len(una_linea) <= largo:
        return una_linea
    return una_linea[: largo - 1] + "…"


def _imprimir_reporte(ruta: Path, resultado: ResultadoAnalisisNLP) -> None:
    fragmentos = resultado.fragmentos_clasificados
    print("=" * 78)
    print(
        f"ERS: {ruta.name}  "
        f"({len(fragmentos)} fragmentos, {len(resultado.anotaciones)} senales)"
    )
    print("-" * 78)
    print(f"{'#':>3}  {'TIPO':<11} {'ID':<6} {'CLASIFICACION':<22} TEXTO")
    for fragmento_clasificado in fragmentos:
        fragmento = fragmento_clasificado.fragmento
        print(
            f"{fragmento.secuencia_orden:>3}  "
            f"{fragmento.tipo_fragmento.value:<11} "
            f"{(fragmento.identificador_ers or '-'):<6} "
            f"{fragmento_clasificado.clasificacion.value:<22} "
            f"{_truncar(fragmento.texto)}"
        )

    por_clasificacion = Counter(r.clasificacion.value for r in fragmentos)
    por_tipo = Counter(r.fragmento.tipo_fragmento.value for r in fragmentos)
    por_senal = Counter(r.tipo_senal.value for r in resultado.anotaciones)
    print("-" * 78)
    print("Por clasificacion: " + _resumen(por_clasificacion))
    print("Por tipo:          " + _resumen(por_tipo))
    print("Por senal NLP:     " + _resumen(por_senal))
    print()


def _resumen(conteo: Counter) -> str:
    return ", ".join(f"{clave}={valor}" for clave, valor in sorted(conteo.items()))


def main(argumentos: Sequence[str]) -> None:
    rutas = _rutas_a_analizar(argumentos)
    if not rutas:
        print(f"No se encontraron ERS para analizar en {DIRECTORIO_ERS}.")
        return

    for ruta in rutas:
        documento = cargar_documento_desde_ruta(ruta)
        resultados = analizar_texto(documento.contenido_extraido)
        _imprimir_reporte(ruta, resultados)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
