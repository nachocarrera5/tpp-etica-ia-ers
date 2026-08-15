from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Pattern, Sequence

from etica_ia_ers.dominio import (
    AnotacionNLP,
    FragmentoDocumental,
    TipoFragmento,
    TipoSenalNLP,
)


@dataclass(frozen=True)
class _ReglaDeteccion:
    identificador: str
    tipo_senal: TipoSenalNLP
    patron: Pattern[str]


def _compilar(expresion: str) -> Pattern[str]:
    return re.compile(rf"(?<!\w)(?:{expresion})(?!\w)", re.IGNORECASE)


_REGLAS: Sequence[_ReglaDeteccion] = (
    _ReglaDeteccion(
        "termino_vago_adecuado",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"adecuad[oa]s?"),
    ),
    _ReglaDeteccion(
        "termino_vago_apropiado",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"apropiad[oa]s?"),
    ),
    _ReglaDeteccion(
        "termino_vago_basico",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"b[aá]sic[oa]s?"),
    ),
    _ReglaDeteccion(
        "termino_vago_completo",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"complet[oa]s?"),
    ),
    _ReglaDeteccion(
        "termino_vago_eficiente",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"eficientes?"),
    ),
    _ReglaDeteccion(
        "termino_vago_optimo",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"[oó]ptim[oa]s?"),
    ),
    _ReglaDeteccion(
        "termino_vago_razonable",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"razonables?"),
    ),
    _ReglaDeteccion(
        "termino_vago_suficiente",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"suficientes?"),
    ),
    _ReglaDeteccion(
        "termino_vago_util",
        TipoSenalNLP.TERMINO_VAGO,
        _compilar(r"[uú]til(?:es)?"),
    ),
    _ReglaDeteccion(
        "ambiguedad_segun_corresponda",
        TipoSenalNLP.AMBIGUEDAD,
        _compilar(r"seg[uú]n\s+corresponda"),
    ),
    _ReglaDeteccion(
        "ambiguedad_segun_sea_necesario",
        TipoSenalNLP.AMBIGUEDAD,
        _compilar(r"seg[uú]n\s+sea\s+necesari[oa]"),
    ),
    _ReglaDeteccion(
        "ambiguedad_segun_proceda",
        TipoSenalNLP.AMBIGUEDAD,
        _compilar(r"seg[uú]n\s+proceda"),
    ),
    _ReglaDeteccion(
        "ambiguedad_cuando_sea_apropiado",
        TipoSenalNLP.AMBIGUEDAD,
        _compilar(r"cuando\s+sea\s+apropiad[oa]"),
    ),
    _ReglaDeteccion(
        "ambiguedad_siempre_que_sea_posible",
        TipoSenalNLP.AMBIGUEDAD,
        _compilar(r"siempre\s+que\s+sea\s+posible"),
    ),
    _ReglaDeteccion(
        "ambiguedad_en_la_medida_de_lo_posible",
        TipoSenalNLP.AMBIGUEDAD,
        _compilar(r"en\s+la\s+medida\s+de\s+lo\s+posible"),
    ),
    _ReglaDeteccion(
        "ambiguedad_en_general",
        TipoSenalNLP.AMBIGUEDAD,
        _compilar(r"en\s+general"),
    ),
)


def detectar_ambiguedades_y_terminos_vagos(
    fragmento: FragmentoDocumental,
) -> List[AnotacionNLP]:
    if fragmento.tipo_fragmento == TipoFragmento.ENCABEZADO:
        return []

    anotaciones = [
        _crear_anotacion(fragmento, regla, coincidencia)
        for regla in _REGLAS
        for coincidencia in regla.patron.finditer(fragmento.texto)
    ]
    return sorted(
        anotaciones,
        key=lambda anotacion: (
            anotacion.posicion_inicio,
            anotacion.posicion_fin,
            anotacion.tipo_senal.value,
        ),
    )


def detectar_en_fragmentos(
    fragmentos: Iterable[FragmentoDocumental],
) -> List[AnotacionNLP]:
    anotaciones: List[AnotacionNLP] = []
    for fragmento in fragmentos:
        anotaciones.extend(detectar_ambiguedades_y_terminos_vagos(fragmento))
    return anotaciones


def _crear_anotacion(
    fragmento: FragmentoDocumental,
    regla: _ReglaDeteccion,
    coincidencia: re.Match[str],
) -> AnotacionNLP:
    inicio, fin = coincidencia.span()
    return AnotacionNLP(
        fragmento_id=fragmento.id,
        tipo_senal=regla.tipo_senal,
        valor_detectado=fragmento.texto[inicio:fin],
        posicion_inicio=inicio,
        posicion_fin=fin,
        metadatos={
            "regla": regla.identificador,
            "metodo": "patron_lexico",
        },
    )
