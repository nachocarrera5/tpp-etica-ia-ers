"""Prueba del pipeline NLP sobre ERS de ejemplo (SCRUM-103).

Ejercita normalizacion, segmentacion y clasificacion de extremo a extremo
cargando las ERS de ejemplo de `ejemplos/ers/` con el mismo cargador que usa
el prototipo. No usa documentos externos ni material academico: las ERS son
material propio, redactado como caso de prueba de los tres dominios de alto
riesgo previstos para la validacion (crediticio, medico y recomendador).
"""

from pathlib import Path
from typing import Dict, List

import pytest

from etica_ia_ers.dominio import (
    FragmentoClasificado,
    TipoClasificacionFragmento,
    TipoFragmento,
)
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.procesamiento_textual_y_nlp import (
    NormalizadorDeTexto,
    TextoVacioError,
    analizar_texto,
    clasificar_fragmentos,
    segmentar,
)

FUNCIONAL = TipoClasificacionFragmento.REQUISITO_FUNCIONAL
NO_FUNCIONAL = TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL
RESTRICCION = TipoClasificacionFragmento.RESTRICCION
CONTEXTO = TipoClasificacionFragmento.CONTEXTO

DIRECTORIO_ERS = Path(__file__).resolve().parents[1] / "ejemplos" / "ers"

# Clasificacion esperada de los fragmentos que el segmentador reconoce como
# REQUISITO (los que llevan verbo normativo). Es la cobertura "correcta" que
# valida esta prueba; las excepciones conocidas se prueban aparte.
CLASIFICACION_ESPERADA_POR_ID: Dict[str, Dict[str, TipoClasificacionFragmento]] = {
    "scoring_crediticio.txt": {
        "2.1": FUNCIONAL,
        "2.2": FUNCIONAL,
        "2.3": FUNCIONAL,
        "3.1": NO_FUNCIONAL,
        "3.2": NO_FUNCIONAL,
        "4.1": RESTRICCION,
    },
    "diagnostico_medico.txt": {
        "2.1": FUNCIONAL,
        "2.2": FUNCIONAL,
        "2.3": FUNCIONAL,
        "3.1": NO_FUNCIONAL,
        "3.2": NO_FUNCIONAL,
        "4.1": RESTRICCION,
    },
    "sistema_recomendador.txt": {
        "2.1": FUNCIONAL,
        "2.2": FUNCIONAL,
        "3.1": NO_FUNCIONAL,
        "3.2": NO_FUNCIONAL,
        "4.1": RESTRICCION,
    },
}

ENCABEZADOS_DE_SECCION_ESPERADOS: Dict[str, set] = {
    "scoring_crediticio.txt": {"1", "1.1", "1.2", "2", "3", "4"},
    "diagnostico_medico.txt": {"1", "2", "3", "4"},
    "sistema_recomendador.txt": {"1", "1.1", "1.2", "2", "3", "4"},
}

PARRAFOS_DE_CONTEXTO_ESPERADOS: Dict[str, int] = {
    "scoring_crediticio.txt": 2,
    "diagnostico_medico.txt": 1,
    "sistema_recomendador.txt": 2,
}

NOMBRES_ERS = sorted(CLASIFICACION_ESPERADA_POR_ID)


def _analizar(nombre: str) -> List[FragmentoClasificado]:
    documento = cargar_documento_desde_ruta(DIRECTORIO_ERS / nombre)
    return analizar_texto(documento.contenido_extraido)


def _clasificacion_por_id(
    resultados: List[FragmentoClasificado],
) -> Dict[str, TipoClasificacionFragmento]:
    return {
        resultado.fragmento.identificador_ers: resultado.clasificacion
        for resultado in resultados
        if resultado.fragmento.tipo_fragmento == TipoFragmento.REQUISITO
        and resultado.fragmento.identificador_ers is not None
    }


def prueba_existen_las_tres_ers_de_ejemplo() -> None:
    encontradas = {ruta.name for ruta in DIRECTORIO_ERS.glob("*.txt")}
    assert set(NOMBRES_ERS) <= encontradas


@pytest.mark.parametrize("nombre", NOMBRES_ERS)
def prueba_el_pipeline_no_falla_y_produce_fragmentos(nombre: str) -> None:
    resultados = _analizar(nombre)

    assert resultados, "El pipeline no produjo fragmentos."
    assert all(resultado.fragmento.texto.strip() for resultado in resultados)
    assert [resultado.fragmento.secuencia_orden for resultado in resultados] == list(
        range(1, len(resultados) + 1)
    )


@pytest.mark.parametrize("nombre", NOMBRES_ERS)
def prueba_los_encabezados_de_seccion_se_reconocen(nombre: str) -> None:
    resultados = _analizar(nombre)
    ids_encabezado = {
        resultado.fragmento.identificador_ers
        for resultado in resultados
        if resultado.fragmento.tipo_fragmento == TipoFragmento.ENCABEZADO
    }

    assert ENCABEZADOS_DE_SECCION_ESPERADOS[nombre] <= ids_encabezado


@pytest.mark.parametrize("nombre", NOMBRES_ERS)
def prueba_los_encabezados_no_reciben_categoria_semantica(nombre: str) -> None:
    resultados = _analizar(nombre)

    for resultado in resultados:
        if resultado.fragmento.tipo_fragmento == TipoFragmento.ENCABEZADO:
            assert resultado.clasificacion == TipoClasificacionFragmento.OTRO


@pytest.mark.parametrize("nombre", NOMBRES_ERS)
def prueba_los_requisitos_se_clasifican_como_se_espera(nombre: str) -> None:
    resultados = _analizar(nombre)
    obtenida = _clasificacion_por_id(resultados)

    for identificador, esperada in CLASIFICACION_ESPERADA_POR_ID[nombre].items():
        assert obtenida.get(identificador) == esperada, (
            f"{nombre} {identificador}: se esperaba {esperada.value}, "
            f"se obtuvo {obtenida.get(identificador)}"
        )


@pytest.mark.parametrize("nombre", NOMBRES_ERS)
def prueba_los_fragmentos_de_restricciones_son_restriccion(nombre: str) -> None:
    resultados = _analizar(nombre)

    for resultado in resultados:
        if (
            resultado.fragmento.seccion_origen == "4. Restricciones"
            and resultado.fragmento.tipo_fragmento != TipoFragmento.ENCABEZADO
        ):
            assert resultado.clasificacion == RESTRICCION


@pytest.mark.parametrize("nombre", NOMBRES_ERS)
def prueba_los_parrafos_de_contexto_se_reconocen(nombre: str) -> None:
    resultados = _analizar(nombre)
    parrafos_contexto = [
        resultado
        for resultado in resultados
        if resultado.fragmento.tipo_fragmento == TipoFragmento.PARRAFO
        and resultado.clasificacion == CONTEXTO
    ]

    assert len(parrafos_contexto) == PARRAFOS_DE_CONTEXTO_ESPERADOS[nombre]


def prueba_las_senales_justifican_cada_clasificacion() -> None:
    resultados = _analizar("scoring_crediticio.txt")

    for resultado in resultados:
        assert resultado.justificacion
        if resultado.clasificacion != TipoClasificacionFragmento.OTRO:
            assert resultado.senales


@pytest.mark.parametrize(
    "nombre, identificador",
    [
        ("scoring_crediticio.txt", "4.2"),
        ("sistema_recomendador.txt", "4.2"),
    ],
)
def prueba_limitacion_conocida_requisito_sin_verbo_normativo(
    nombre: str, identificador: str
) -> None:
    """Limitacion conocida del segmentador (SCRUM-99/SCRUM-102).

    Un requisito redactado sin verbo normativo (debe/debera) y suficientemente
    corto ("El sistema unicamente podra...", "Queda prohibido...") se segmenta
    como ENCABEZADO y por lo tanto no recibe categoria semantica. Queda
    registrado como hallazgo en `ejemplos/HALLAZGOS-nlp.md`. Si el segmentador
    se mejora para cubrir estas formas, esta prueba fallara y hay que
    actualizarla.
    """
    resultados = _analizar(nombre)
    fragmento = next(
        resultado
        for resultado in resultados
        if resultado.fragmento.identificador_ers == identificador
    )

    assert fragmento.fragmento.tipo_fragmento == TipoFragmento.ENCABEZADO
    assert fragmento.clasificacion == TipoClasificacionFragmento.OTRO


def prueba_analizar_texto_equivale_al_pipeline_manual() -> None:
    documento = cargar_documento_desde_ruta(
        DIRECTORIO_ERS / "scoring_crediticio.txt"
    )
    texto = documento.contenido_extraido

    esperado = clasificar_fragmentos(
        segmentar(NormalizadorDeTexto().normalizar(texto).normalizado)
    )
    obtenido = analizar_texto(texto)

    assert [r.clasificacion for r in obtenido] == [r.clasificacion for r in esperado]
    assert [r.fragmento.texto for r in obtenido] == [
        r.fragmento.texto for r in esperado
    ]


def prueba_analizar_texto_rechaza_texto_vacio() -> None:
    with pytest.raises(TextoVacioError):
        analizar_texto("   \n\n   ")
