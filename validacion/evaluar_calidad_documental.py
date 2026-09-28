"""Evalua cobertura, ambiguedad, verificabilidad y evidencia documental."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from etica_ia_ers.dominio import TipoFragmento, TipoSenalNLP
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto


TIPOS_AMBIGUEDAD = {
    TipoSenalNLP.AMBIGUEDAD,
    TipoSenalNLP.TERMINO_VAGO,
}


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


def _porcentaje(numerador: int, denominador: int) -> float:
    return round(100 * numerador / denominador, 2) if denominador else 0.0


def evaluar(
    corpus_dir: Path,
    resultados_dir: Path,
    salida: Path,
) -> None:
    base = Path(__file__).resolve().parent
    corpus = _leer_csv(base / "corpus.csv")
    dimensiones = _leer_csv(resultados_dir / "resultados_dimensiones.csv")
    guardrails = _leer_csv(resultados_dir / "resultados_guardrails.csv")
    manifiesto = json.loads(
        (resultados_dir / "manifiesto.json").read_text(encoding="utf-8")
    )
    salida.mkdir(parents=True, exist_ok=True)

    hashes = _calcular_hashes_corpus(corpus, corpus_dir)
    ambiguedad, reglas = _evaluar_ambiguedad(corpus, corpus_dir)
    cobertura = _evaluar_cobertura(corpus, dimensiones)
    verificabilidad = _evaluar_verificabilidad(corpus, guardrails)
    evidencia = _evaluar_evidencia(corpus, guardrails)
    por_tipo = _evaluar_por_tipo(
        ambiguedad,
        cobertura,
        verificabilidad,
        evidencia,
    )
    resumen = _crear_resumen(
        ambiguedad,
        cobertura,
        verificabilidad,
        evidencia,
        guardrails,
        por_tipo,
    )
    resumen = {
        "linea_base": {
            "commit": manifiesto["commit"],
            "fecha_utc": manifiesto["fecha_utc"],
            "documentos_con_hash": len(hashes),
        },
        **resumen,
    }

    _escribir_csv(
        salida / "ambiguedad_por_documento.csv",
        ambiguedad,
        list(ambiguedad[0]),
    )
    _escribir_csv(
        salida / "ambiguedad_por_regla.csv",
        reglas,
        list(reglas[0]),
    )
    _escribir_csv(
        salida / "cobertura_por_documento.csv",
        cobertura,
        list(cobertura[0]),
    )
    _escribir_csv(
        salida / "verificabilidad_por_documento.csv",
        verificabilidad,
        list(verificabilidad[0]),
    )
    _escribir_csv(
        salida / "evidencia_por_documento.csv",
        evidencia,
        list(evidencia[0]),
    )
    _escribir_csv(
        salida / "resumen_por_tipo_documento.csv",
        por_tipo,
        list(por_tipo[0]),
    )
    _escribir_csv(
        salida / "hashes_corpus.csv",
        hashes,
        list(hashes[0]),
    )
    (salida / "resumen_calidad_documental.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _calcular_hashes_corpus(
    corpus: list[dict[str, str]], corpus_dir: Path
) -> list[dict]:
    filas = []
    for item in corpus:
        ruta = corpus_dir / item["archivo"]
        contenido = ruta.read_bytes()
        filas.append(
            {
                "documento": item["documento"],
                "archivo": item["archivo"],
                "bytes": len(contenido),
                "sha256": hashlib.sha256(contenido).hexdigest(),
            }
        )
    return filas


def _evaluar_ambiguedad(
    corpus: list[dict[str, str]], corpus_dir: Path
) -> tuple[list[dict], list[dict]]:
    filas = []
    reglas: Counter[tuple[str, str, str]] = Counter()
    for item in corpus:
        documento = cargar_documento_desde_ruta(corpus_dir / item["archivo"])
        resultado = analizar_texto(documento.contenido_extraido)
        palabras = len(
            re.findall(r"\w+", resultado.texto_normalizado.normalizado)
        )
        fragmentos = [
            clasificado.fragmento
            for clasificado in resultado.fragmentos_clasificados
            if clasificado.fragmento.tipo_fragmento != TipoFragmento.ENCABEZADO
        ]
        anotaciones = [
            anotacion
            for anotacion in resultado.anotaciones
            if anotacion.tipo_senal in TIPOS_AMBIGUEDAD
        ]
        fragmentos_afectados = {
            anotacion.fragmento_id for anotacion in anotaciones
        }
        vagos = sum(
            anotacion.tipo_senal == TipoSenalNLP.TERMINO_VAGO
            for anotacion in anotaciones
        )
        ambiguos = len(anotaciones) - vagos
        filas.append(
            {
                "documento": item["documento"],
                "tipo_documento": item["tipo"],
                "fragmentos_evaluables": len(fragmentos),
                "palabras_normalizadas": palabras,
                "fragmentos_con_senal": len(fragmentos_afectados),
                "terminos_vagos": vagos,
                "expresiones_ambiguas": ambiguos,
                "total_senales": len(anotaciones),
                "fragmentos_con_senal_pct": _porcentaje(
                    len(fragmentos_afectados), len(fragmentos)
                ),
                "senales_cada_100_fragmentos": _porcentaje(
                    len(anotaciones), len(fragmentos)
                ),
                "senales_cada_1000_palabras": round(
                    1000 * len(anotaciones) / palabras, 2
                )
                if palabras
                else 0.0,
            }
        )
        for anotacion in anotaciones:
            reglas[
                (
                    item["documento"],
                    anotacion.tipo_senal.value,
                    str(anotacion.metadatos.get("regla", "DESCONOCIDA")),
                )
            ] += 1

    filas_reglas = [
        {
            "documento": documento,
            "tipo_senal": tipo_senal,
            "regla": regla,
            "cantidad": cantidad,
        }
        for (documento, tipo_senal, regla), cantidad in sorted(reglas.items())
    ]
    if not filas_reglas:
        filas_reglas.append(
            {
                "documento": "",
                "tipo_senal": "",
                "regla": "",
                "cantidad": 0,
            }
        )
    return filas, filas_reglas


def _evaluar_cobertura(
    corpus: list[dict[str, str]], dimensiones: list[dict[str, str]]
) -> list[dict]:
    por_documento = _agrupar_por_documento(dimensiones)
    filas = []
    for item in corpus:
        resultados = por_documento[item["documento"]]
        niveles = Counter(fila["nivel_obtenido"] for fila in resultados)
        evaluadas = len(resultados)
        no_ausentes = niveles["PARCIAL"] + niveles["EXPLICITO"]
        filas.append(
            {
                "documento": item["documento"],
                "tipo_documento": item["tipo"],
                "dimensiones_evaluadas": evaluadas,
                "ausentes": niveles["AUSENTE"],
                "parciales": niveles["PARCIAL"],
                "explicitas": niveles["EXPLICITO"],
                "cobertura_no_ausente_pct": _porcentaje(
                    no_ausentes, evaluadas
                ),
                "cobertura_explicita_pct": _porcentaje(
                    niveles["EXPLICITO"], evaluadas
                ),
            }
        )
    return filas


def _evaluar_verificabilidad(
    corpus: list[dict[str, str]], guardrails: list[dict[str, str]]
) -> list[dict]:
    verificables = [
        fila for fila in guardrails if "-VERIF-" in fila["guardrail"]
    ]
    por_documento = _agrupar_por_documento(verificables)
    filas = []
    for item in corpus:
        resultados = por_documento[item["documento"]]
        niveles = Counter(fila["nivel_obtenido"] for fila in resultados)
        con_evidencia = niveles["PARCIAL"] + niveles["EXPLICITO"]
        filas.append(
            {
                "documento": item["documento"],
                "tipo_documento": item["tipo"],
                "guardrails_verificabilidad": len(resultados),
                "ausentes": niveles["AUSENTE"],
                "parciales": niveles["PARCIAL"],
                "explicitos": niveles["EXPLICITO"],
                "con_evidencia": con_evidencia,
                "con_evidencia_pct": _porcentaje(
                    con_evidencia, len(resultados)
                ),
            }
        )
    return filas


def _evaluar_evidencia(
    corpus: list[dict[str, str]], guardrails: list[dict[str, str]]
) -> list[dict]:
    por_documento = _agrupar_por_documento(guardrails)
    filas = []
    for item in corpus:
        resultados = por_documento[item["documento"]]
        cantidades = [int(fila["cantidad_evidencias"]) for fila in resultados]
        con_evidencia = [cantidad for cantidad in cantidades if cantidad > 0]
        inconsistencias = sum(
            (fila["nivel_obtenido"] == "AUSENTE")
            != (int(fila["cantidad_evidencias"]) == 0)
            for fila in resultados
        )
        filas.append(
            {
                "documento": item["documento"],
                "tipo_documento": item["tipo"],
                "aplicaciones_guardrail": len(resultados),
                "aplicaciones_con_evidencia": len(con_evidencia),
                "aplicaciones_con_evidencia_pct": _porcentaje(
                    len(con_evidencia), len(resultados)
                ),
                "vinculos_evidencia": sum(cantidades),
                "mediana_vinculos_si_hay_evidencia": (
                    statistics.median(con_evidencia) if con_evidencia else 0
                ),
                "maximo_vinculos_en_un_guardrail": max(cantidades, default=0),
                "inconsistencias_nivel_evidencia": inconsistencias,
            }
        )
    return filas


def _agrupar_por_documento(
    filas: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    agrupadas: dict[str, list[dict[str, str]]] = defaultdict(list)
    for fila in filas:
        agrupadas[fila["documento"]].append(fila)
    return agrupadas


def _evaluar_por_tipo(
    ambiguedad: list[dict],
    cobertura: list[dict],
    verificabilidad: list[dict],
    evidencia: list[dict],
) -> list[dict]:
    filas = []
    for tipo in ("SINTETICA", "REAL"):
        amb = [fila for fila in ambiguedad if fila["tipo_documento"] == tipo]
        cob = [fila for fila in cobertura if fila["tipo_documento"] == tipo]
        ver = [
            fila for fila in verificabilidad if fila["tipo_documento"] == tipo
        ]
        evi = [fila for fila in evidencia if fila["tipo_documento"] == tipo]
        palabras = sum(fila["palabras_normalizadas"] for fila in amb)
        senales = sum(fila["total_senales"] for fila in amb)
        dimensiones = sum(fila["dimensiones_evaluadas"] for fila in cob)
        ausentes = sum(fila["ausentes"] for fila in cob)
        explicitas = sum(fila["explicitas"] for fila in cob)
        verificables = sum(fila["guardrails_verificabilidad"] for fila in ver)
        verificables_con_evidencia = sum(
            fila["con_evidencia"] for fila in ver
        )
        aplicaciones = sum(fila["aplicaciones_guardrail"] for fila in evi)
        aplicaciones_con_evidencia = sum(
            fila["aplicaciones_con_evidencia"] for fila in evi
        )
        filas.append(
            {
                "tipo_documento": tipo,
                "documentos": len(amb),
                "dimensiones": dimensiones,
                "cobertura_no_ausente_pct": _porcentaje(
                    dimensiones - ausentes, dimensiones
                ),
                "cobertura_explicita_pct": _porcentaje(
                    explicitas, dimensiones
                ),
                "senales_ambiguedad_vaguedad": senales,
                "senales_cada_1000_palabras": (
                    round(1000 * senales / palabras, 2) if palabras else 0.0
                ),
                "verificabilidad_con_evidencia_pct": _porcentaje(
                    verificables_con_evidencia, verificables
                ),
                "aplicaciones_con_evidencia_pct": _porcentaje(
                    aplicaciones_con_evidencia, aplicaciones
                ),
            }
        )
    return filas


def _crear_resumen(
    ambiguedad: list[dict],
    cobertura: list[dict],
    verificabilidad: list[dict],
    evidencia: list[dict],
    guardrails: list[dict[str, str]],
    por_tipo: list[dict],
) -> dict:
    total_fragmentos = sum(fila["fragmentos_evaluables"] for fila in ambiguedad)
    total_palabras = sum(fila["palabras_normalizadas"] for fila in ambiguedad)
    fragmentos_con_senal = sum(
        fila["fragmentos_con_senal"] for fila in ambiguedad
    )
    total_senales = sum(fila["total_senales"] for fila in ambiguedad)
    dimensiones = sum(fila["dimensiones_evaluadas"] for fila in cobertura)
    dimensiones_ausentes = sum(fila["ausentes"] for fila in cobertura)
    dimensiones_explicitas = sum(fila["explicitas"] for fila in cobertura)
    total_verificabilidad = sum(
        fila["guardrails_verificabilidad"] for fila in verificabilidad
    )
    verificabilidad_con_evidencia = sum(
        fila["con_evidencia"] for fila in verificabilidad
    )
    aplicaciones_con_evidencia = sum(
        fila["aplicaciones_con_evidencia"] for fila in evidencia
    )
    total_vinculos = sum(fila["vinculos_evidencia"] for fila in evidencia)

    return {
        "corpus": {
            "documentos": len(cobertura),
            "dimensiones": dimensiones,
            "aplicaciones_guardrail": len(guardrails),
        },
        "cobertura_etica": {
            "dimensiones_ausentes": dimensiones_ausentes,
            "dimensiones_parciales": sum(
                fila["parciales"] for fila in cobertura
            ),
            "dimensiones_explicitas": dimensiones_explicitas,
            "cobertura_no_ausente_pct": _porcentaje(
                dimensiones - dimensiones_ausentes, dimensiones
            ),
            "cobertura_explicita_pct": _porcentaje(
                dimensiones_explicitas, dimensiones
            ),
        },
        "ambiguedad": {
            "fragmentos_evaluables": total_fragmentos,
            "palabras_normalizadas": total_palabras,
            "fragmentos_con_senal": fragmentos_con_senal,
            "fragmentos_con_senal_pct": _porcentaje(
                fragmentos_con_senal, total_fragmentos
            ),
            "terminos_vagos": sum(fila["terminos_vagos"] for fila in ambiguedad),
            "expresiones_ambiguas": sum(
                fila["expresiones_ambiguas"] for fila in ambiguedad
            ),
            "total_senales": total_senales,
            "senales_cada_1000_palabras": (
                round(1000 * total_senales / total_palabras, 2)
                if total_palabras
                else 0.0
            ),
        },
        "verificabilidad": {
            "aplicaciones": total_verificabilidad,
            "con_evidencia": verificabilidad_con_evidencia,
            "con_evidencia_pct": _porcentaje(
                verificabilidad_con_evidencia, total_verificabilidad
            ),
        },
        "evidencia_documental": {
            "aplicaciones_con_evidencia": aplicaciones_con_evidencia,
            "aplicaciones_con_evidencia_pct": _porcentaje(
                aplicaciones_con_evidencia, len(guardrails)
            ),
            "vinculos_evidencia": total_vinculos,
            "inconsistencias_nivel_evidencia": sum(
                fila["inconsistencias_nivel_evidencia"] for fila in evidencia
            ),
        },
        "por_tipo_documento": por_tipo,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument(
        "--resultados",
        type=Path,
        default=Path(__file__).resolve().parent / "resultados",
    )
    parser.add_argument("--salida", type=Path, required=True)
    argumentos = parser.parse_args()
    evaluar(argumentos.corpus, argumentos.resultados, argumentos.salida)


if __name__ == "__main__":
    main()
