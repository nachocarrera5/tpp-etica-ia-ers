from __future__ import annotations

import re
from typing import List, Optional

from etica_ia_ers.dominio import FragmentoDocumental, TipoFragmento
from etica_ia_ers.dominio.fragmento import _AMBIGUEDADES, _TERMINOS_VAGOS


_PATRON_ENCABEZADO = re.compile(
    r"^(\d+(?:\.\d+)*)\.\s+(.+)$"
)

_PATRON_INICIO_ESTRUCTURAL = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.\s+|-\s+)"
)

_PATRON_ITEM_LISTA = re.compile(r"^- (.+)", re.DOTALL)
_PATRON_VERBO_NORMATIVO = re.compile(
    r"\b(?:debe|deben|debera|deberan|deberá|deberán|"
    r"tendra\s+que|tendran\s+que|tendrá\s+que|tendrán\s+que)\b",
    re.IGNORECASE,
)

_LIMITE_LARGO_ENCABEZADO = 120


def segmentar(texto_normalizado: str) -> List[FragmentoDocumental]:
    if not texto_normalizado or not texto_normalizado.strip():
        raise ValueError("El texto a segmentar esta vacio.")

    bloques = _dividir_en_bloques(texto_normalizado)
    fragmentos: List[FragmentoDocumental] = []
    seccion_actual: Optional[str] = None
    orden = 0

    for texto_bloque, pos_inicio, pos_fin in bloques:
        tipo, identificador = _clasificar_bloque(texto_bloque)

        if tipo == TipoFragmento.ENCABEZADO:
            seccion_actual = texto_bloque.strip()

        texto_limpio = texto_bloque.strip()
        terminos_vagos = tuple(
            termino
            for termino in sorted(_TERMINOS_VAGOS)
            if termino in texto_limpio.lower()
        )
        ambiguedades = tuple(
            expresion
            for expresion in sorted(_AMBIGUEDADES)
            if expresion in texto_limpio.lower()
        )

        orden += 1
        fragmentos.append(
            FragmentoDocumental(
                secuencia_orden=orden,
                tipo_fragmento=tipo,
                texto=texto_limpio,
                seccion_origen=seccion_actual,
                identificador_ers=identificador,
                posicion_inicio=pos_inicio,
                posicion_fin=pos_fin,
                terminos_vagos=terminos_vagos,
                ambiguedades=ambiguedades,
            )
        )

    return fragmentos


def _dividir_en_bloques(texto: str) -> List[tuple]:
    bloques = []
    inicio_bloque: Optional[int] = None
    fin_bloque: Optional[int] = None
    posicion = 0

    for linea_con_salto in texto.splitlines(keepends=True):
        linea = linea_con_salto.rstrip("\r\n")
        inicio_linea = posicion
        fin_linea = inicio_linea + len(linea)
        posicion += len(linea_con_salto)

        if not linea.strip():
            if inicio_bloque is not None and fin_bloque is not None:
                bloques.append(
                    _crear_bloque(texto, inicio_bloque, fin_bloque)
                )
                inicio_bloque = None
                fin_bloque = None
            continue

        inicia_estructura = _PATRON_INICIO_ESTRUCTURAL.match(linea) is not None
        if inicia_estructura and inicio_bloque is not None and fin_bloque is not None:
            bloques.append(_crear_bloque(texto, inicio_bloque, fin_bloque))
            inicio_bloque = inicio_linea
        elif inicio_bloque is None:
            inicio_bloque = inicio_linea

        fin_bloque = fin_linea

    if inicio_bloque is not None and fin_bloque is not None:
        bloques.append(_crear_bloque(texto, inicio_bloque, fin_bloque))

    return bloques


def _crear_bloque(texto: str, inicio: int, fin: int) -> tuple:
    while inicio < fin and texto[inicio].isspace():
        inicio += 1
    while fin > inicio and texto[fin - 1].isspace():
        fin -= 1
    return texto[inicio:fin], inicio, fin


def _clasificar_bloque(texto: str) -> tuple:
    texto_limpio = texto.strip()
    primera_linea = texto_limpio.split("\n")[0]

    if _PATRON_ITEM_LISTA.match(texto_limpio):
        return TipoFragmento.ITEM_LISTA, None

    match_num = _PATRON_ENCABEZADO.match(primera_linea)
    if match_num:
        numeracion = match_num.group(1)
        contenido_linea = match_num.group(2)

        es_corto = len(primera_linea) <= _LIMITE_LARGO_ENCABEZADO
        es_unilinea = "\n" not in texto_limpio
        profundidad_numeracion = numeracion.count(".") + 1

        contiene_verbo_normativo = bool(
            _PATRON_VERBO_NORMATIVO.search(contenido_linea)
        )

        if contiene_verbo_normativo:
            return TipoFragmento.REQUISITO, numeracion

        if es_corto and es_unilinea and profundidad_numeracion <= 2:
            return TipoFragmento.ENCABEZADO, numeracion

        if profundidad_numeracion >= 2:
            return TipoFragmento.REQUISITO, numeracion

        if not es_unilinea or len(primera_linea) > _LIMITE_LARGO_ENCABEZADO:
            return TipoFragmento.REQUISITO, numeracion

        return TipoFragmento.ENCABEZADO, numeracion

    return TipoFragmento.PARRAFO, None
