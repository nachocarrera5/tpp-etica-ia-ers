from __future__ import annotations
import re
from typing import List, Optional
from etica_ia_ers.dominio import FragmentoDocumental, TipoFragmento



_PATRON_ENCABEZADO = re.compile(
    r"^(\d+(?:\.\d+)*)\.\s+(.+)$"
)

_PATRON_REQUISITO = re.compile(
    r"^(\d+(?:\.\d+)+)\.\s+(.+)",
    re.DOTALL,
)

_PATRON_ITEM_LISTA = re.compile(r"^- (.+)", re.DOTALL)

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

        orden += 1
        fragmentos.append(
            FragmentoDocumental(
                secuencia_orden=orden,
                tipo_fragmento=tipo,
                texto=texto_bloque.strip(),
                seccion_origen=seccion_actual,
                identificador_ers=identificador,
                posicion_inicio=pos_inicio,
                posicion_fin=pos_fin,
            )
        )

    return fragmentos


def _dividir_en_bloques(texto: str) -> List[tuple]:

    bloques = []
    posicion = 0

    for parte in re.split(r"\n\n", texto):
        if not parte.strip():
            posicion += len(parte) + 2  
            continue

        inicio = texto.index(parte, posicion)
        fin = inicio + len(parte)
        bloques.append((parte, inicio, fin))
        posicion = fin + 2  

    return bloques


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

        if es_corto and es_unilinea and profundidad_numeracion <= 2:
            return TipoFragmento.ENCABEZADO, numeracion

        if profundidad_numeracion >= 2:
            return TipoFragmento.REQUISITO, numeracion

        if not es_unilinea or len(primera_linea) > _LIMITE_LARGO_ENCABEZADO:
            return TipoFragmento.REQUISITO, numeracion

        return TipoFragmento.ENCABEZADO, numeracion

    return TipoFragmento.PARRAFO, None
