from __future__ import annotations

import re
from functools import lru_cache
from importlib.metadata import version
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from spacy.language import Language
from spacy.tokens import Doc, Token

from etica_ia_ers.dominio import (
    AnotacionNLP,
    FragmentoDocumental,
    TipoFragmento,
    TipoSenalNLP,
)
from etica_ia_ers.procesamiento_textual_y_nlp.errores import (
    ModeloNLPNoDisponibleError,
)


_NOMBRE_MODELO = "es_core_news_sm"

_LEMAS_ACTOR = {
    "administrador",
    "afectado",
    "analista",
    "aplicacion",
    "area",
    "auditor",
    "autoridad",
    "cliente",
    "comunidad",
    "desarrollador",
    "equipo",
    "grupo",
    "motor",
    "operador",
    "organizacion",
    "paciente",
    "persona",
    "personal",
    "plataforma",
    "poblacion",
    "profesional",
    "proveedor",
    "responsable",
    "sistema",
    "solicitante",
    "supervisor",
    "usuario",
}

_DEPENDENCIAS_NOMINALES = {
    "amod",
    "appos",
    "compound",
    "det",
    "fixed",
    "flat",
    "nmod",
    "nummod",
}

_DEPENDENCIAS_ACCION = {
    "advmod",
    "aux",
    "ccomp",
    "iobj",
    "neg",
    "obj",
    "obl",
    "xcomp",
}

_DEPENDENCIAS_VERBO_PRINCIPAL = {"ROOT", "ccomp", "conj", "xcomp"}

_PATRON_CONDICION = re.compile(
    r"\b(?:siempre que|a menos que|en caso de|una vez que|hasta que|"
    r"dentro de|antes de|despu[eé]s de|cuando|mientras|ante|si)\b",
    re.IGNORECASE,
)

_TIPOS_CONDICION = {
    "si": "condicional",
    "siempre que": "condicional",
    "a menos que": "excepcion",
    "en caso de": "evento",
    "ante": "evento",
    "cuando": "temporal",
    "mientras": "temporal",
    "una vez que": "temporal",
    "hasta que": "temporal",
    "dentro de": "temporal",
    "antes de": "temporal",
    "despues de": "temporal",
}

_PRIORIDAD_ROL = {
    "agente_pasivo": 5,
    "sujeto": 4,
    "destinatario": 3,
    "afectado": 2,
    "entidad": 1,
    "mencion": 0,
}


def _importar_modelo() -> Any:
    import es_core_news_sm

    return es_core_news_sm


@lru_cache(maxsize=1)
def _cargar_modelo() -> Language:
    try:
        paquete_modelo = _importar_modelo()
        return paquete_modelo.load()
    except (ImportError, OSError) as error:
        raise ModeloNLPNoDisponibleError(
            "No se pudo cargar es_core_news_sm. Instale el proyecto con "
            "'python3 -m pip install -e .'."
        ) from error


def extraer_actores_acciones_condiciones(
    fragmento: FragmentoDocumental,
) -> List[AnotacionNLP]:
    if fragmento.tipo_fragmento == TipoFragmento.ENCABEZADO:
        return []

    doc = _cargar_modelo()(fragmento.texto)
    condiciones = _extraer_condiciones(fragmento)
    rangos_condiciones = [
        (anotacion.posicion_inicio, anotacion.posicion_fin)
        for anotacion in condiciones
    ]
    actores = _extraer_actores(fragmento, doc)
    acciones = _extraer_acciones(fragmento, doc, rangos_condiciones)

    anotaciones = _deduplicar(actores + acciones + condiciones)
    return sorted(
        anotaciones,
        key=lambda item: (
            item.posicion_inicio,
            item.posicion_fin,
            item.tipo_senal.value,
        ),
    )


def extraer_de_fragmentos(
    fragmentos: Iterable[FragmentoDocumental],
) -> List[AnotacionNLP]:
    anotaciones: List[AnotacionNLP] = []
    for fragmento in fragmentos:
        anotaciones.extend(extraer_actores_acciones_condiciones(fragmento))
    return anotaciones


def _extraer_actores(
    fragmento: FragmentoDocumental,
    doc: Doc,
) -> List[AnotacionNLP]:
    candidatos: Dict[Tuple[int, int], Tuple[str, Token, str]] = {}

    for token in doc:
        if token.pos_ not in {"NOUN", "PROPN"}:
            continue

        lema = _normalizar_lema(token.lemma_)
        if lema not in _LEMAS_ACTOR:
            continue

        rol = _rol_actor(token)
        inicio, fin = _rango_nominal(token)
        actual = candidatos.get((inicio, fin))
        if actual is None or _PRIORIDAD_ROL[rol] > _PRIORIDAD_ROL[actual[0]]:
            candidatos[(inicio, fin)] = (rol, token, "dependencia_y_lexico")

    for entidad in doc.ents:
        if entidad.label_ not in {"ORG", "PER"}:
            continue
        clave = (entidad.start_char, entidad.end_char)
        if clave not in candidatos:
            candidatos[clave] = ("entidad", entidad.root, "entidad_nombrada")

    return [
        _crear_anotacion(
            fragmento,
            TipoSenalNLP.ACTOR,
            inicio,
            fin,
            {
                "rol": rol,
                "lema_raiz": token.lemma_,
                "dependencia": token.dep_,
                "regla": regla,
            },
        )
        for (inicio, fin), (rol, token, regla) in candidatos.items()
    ]


def _rol_actor(token: Token) -> str:
    if _es_construccion_pasiva(token.head) and any(
        hijo.dep_ == "case" and hijo.lemma_.casefold() == "por"
        for hijo in token.children
    ):
        return "agente_pasivo"
    if token.dep_ in {"obj", "iobj"}:
        return "destinatario"
    if token.dep_.startswith("nsubj"):
        if _es_construccion_pasiva(token.head):
            return "afectado"
        return "sujeto"
    return "mencion"


def _es_construccion_pasiva(verbo: Token) -> bool:
    return verbo.pos_ == "VERB" and any(
        hijo.pos_ == "AUX" and hijo.lemma_.casefold() == "ser"
        for hijo in verbo.children
    )


def _rango_nominal(token: Token) -> Tuple[int, int]:
    incluidos = {token.i}
    pendientes = [token]
    while pendientes:
        actual = pendientes.pop()
        for hijo in actual.children:
            if hijo.dep_ in _DEPENDENCIAS_NOMINALES:
                incluidos.add(hijo.i)
                pendientes.append(hijo)

    primero = token.doc[min(incluidos)]
    ultimo = token.doc[max(incluidos)]
    return primero.idx, ultimo.idx + len(ultimo)


def _extraer_acciones(
    fragmento: FragmentoDocumental,
    doc: Doc,
    rangos_condiciones: Sequence[Tuple[int, int]],
) -> List[AnotacionNLP]:
    anotaciones = []
    for token in doc:
        if token.pos_ != "VERB" or token.dep_ not in _DEPENDENCIAS_VERBO_PRINCIPAL:
            continue
        if _esta_en_rangos(token.idx, rangos_condiciones):
            continue

        inicio, fin = _rango_accion(token, rangos_condiciones)
        anotaciones.append(
            _crear_anotacion(
                fragmento,
                TipoSenalNLP.ACCION,
                inicio,
                fin,
                {
                    "lema": token.lemma_,
                    "dependencia": token.dep_,
                    "verbo_normativo": any(
                        hijo.pos_ == "AUX" and hijo.lemma_ == "deber"
                        for hijo in token.children
                    ),
                    "regla": "verbo_principal_y_complementos",
                },
            )
        )
    return anotaciones


def _rango_accion(
    verbo: Token,
    rangos_condiciones: Sequence[Tuple[int, int]],
) -> Tuple[int, int]:
    incluidos: Set[int] = {verbo.i}
    for hijo in verbo.children:
        if hijo.dep_ not in _DEPENDENCIAS_ACCION:
            continue
        for descendiente in hijo.subtree:
            if not _esta_en_rangos(descendiente.idx, rangos_condiciones):
                incluidos.add(descendiente.i)

    primero = verbo.doc[min(incluidos)]
    ultimo = verbo.doc[max(incluidos)]
    return primero.idx, ultimo.idx + len(ultimo)


def _extraer_condiciones(
    fragmento: FragmentoDocumental,
) -> List[AnotacionNLP]:
    texto = fragmento.texto
    coincidencias = list(_PATRON_CONDICION.finditer(texto))
    anotaciones = []
    for indice, coincidencia in enumerate(coincidencias):
        siguiente_inicio = (
            coincidencias[indice + 1].start()
            if indice + 1 < len(coincidencias)
            else len(texto)
        )
        fin = _fin_condicion(texto, coincidencia.end(), siguiente_inicio)
        fin = _recortar_fin(texto, coincidencia.start(), fin)
        marcador = _normalizar_lema(coincidencia.group(0))
        anotaciones.append(
            _crear_anotacion(
                fragmento,
                TipoSenalNLP.CONDICION,
                coincidencia.start(),
                fin,
                {
                    "marcador": coincidencia.group(0),
                    "tipo_condicion": _TIPOS_CONDICION[marcador],
                    "regla": "marcador_condicional",
                },
            )
        )
    return anotaciones


def _fin_condicion(texto: str, desde: int, limite: int) -> int:
    finales = [
        posicion
        for separador in (",", ";", ".", "\n")
        if (posicion := texto.find(separador, desde, limite)) != -1
    ]
    return min(finales) if finales else limite


def _recortar_fin(texto: str, inicio: int, fin: int) -> int:
    while fin > inicio and texto[fin - 1].isspace():
        fin -= 1
    return fin


def _esta_en_rangos(posicion: int, rangos: Sequence[Tuple[int, int]]) -> bool:
    return any(inicio <= posicion < fin for inicio, fin in rangos)


def _crear_anotacion(
    fragmento: FragmentoDocumental,
    tipo: TipoSenalNLP,
    inicio: int,
    fin: int,
    metadatos: Dict[str, Any],
) -> AnotacionNLP:
    metadatos_completos = {
        "procesador": "spacy_reglas",
        "version_herramienta": version("spacy"),
        "modelo": _NOMBRE_MODELO,
        "version_modelo": version("es-core-news-sm"),
        **metadatos,
    }
    return AnotacionNLP(
        fragmento_id=fragmento.id,
        tipo_senal=tipo,
        valor_detectado=fragmento.texto[inicio:fin],
        posicion_inicio=inicio,
        posicion_fin=fin,
        confianza=None,
        metadatos=metadatos_completos,
    )


def _deduplicar(anotaciones: Iterable[AnotacionNLP]) -> List[AnotacionNLP]:
    unicas: Dict[Tuple[TipoSenalNLP, int, int], AnotacionNLP] = {}
    for anotacion in anotaciones:
        clave = (
            anotacion.tipo_senal,
            anotacion.posicion_inicio,
            anotacion.posicion_fin,
        )
        unicas.setdefault(clave, anotacion)
    return list(unicas.values())


def _normalizar_lema(lema: str) -> str:
    reemplazos = str.maketrans("áéíóúüñ", "aeiouun")
    return lema.casefold().translate(reemplazos)
