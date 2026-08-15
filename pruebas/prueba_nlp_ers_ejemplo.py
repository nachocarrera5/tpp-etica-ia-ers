"""Prueba del pipeline NLP completo sobre ERS de ejemplo (SCRUM-103).

Ejercita carga, normalizacion, segmentacion, clasificacion, extraccion de
actores, acciones y condiciones, y deteccion de ambiguedad y vaguedad. Las ERS
son material propio de los dominios crediticio, medico y recomendador.
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import pytest

from etica_ia_ers.dominio import (
    FragmentoClasificado,
    ResultadoAnalisisNLP,
    TipoClasificacionFragmento,
    TipoFragmento,
    TipoSenalNLP,
)
from etica_ia_ers.entrada_documental import cargar_documento_desde_ruta
from etica_ia_ers.procesamiento_textual_y_nlp import (
    NormalizadorDeTexto,
    TextoVacioError,
    analizar_texto,
    clasificar_fragmentos,
    detectar_en_fragmentos,
    extraer_de_fragmentos,
    segmentar,
)

FUNCIONAL = TipoClasificacionFragmento.REQUISITO_FUNCIONAL
NO_FUNCIONAL = TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL
RESTRICCION = TipoClasificacionFragmento.RESTRICCION
CONTEXTO = TipoClasificacionFragmento.CONTEXTO

DIRECTORIO_ERS = Path(__file__).resolve().parents[1] / "ejemplos" / "ers"

# Clasificacion esperada de los requisitos identificados en cada ERS.
CLASIFICACION_ESPERADA_POR_ID: Dict[str, Dict[str, TipoClasificacionFragmento]] = {
    "scoring_crediticio.txt": {
        "2.1": FUNCIONAL,
        "2.2": FUNCIONAL,
        "2.3": FUNCIONAL,
        "3.1": NO_FUNCIONAL,
        "3.2": NO_FUNCIONAL,
        "4.1": RESTRICCION,
        "4.2": RESTRICCION,
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
        "4.2": RESTRICCION,
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


@lru_cache(maxsize=None)
def _resultado(nombre: str) -> ResultadoAnalisisNLP:
    documento = cargar_documento_desde_ruta(DIRECTORIO_ERS / nombre)
    return analizar_texto(documento.contenido_extraido)


def _analizar(nombre: str) -> List[FragmentoClasificado]:
    return list(_resultado(nombre).fragmentos_clasificados)


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
def prueba_reconoce_restricciones_con_otras_formas_normativas(
    nombre: str, identificador: str
) -> None:
    resultados = _analizar(nombre)
    fragmento = next(
        resultado
        for resultado in resultados
        if resultado.fragmento.identificador_ers == identificador
    )

    assert fragmento.fragmento.tipo_fragmento == TipoFragmento.REQUISITO
    assert fragmento.clasificacion == TipoClasificacionFragmento.RESTRICCION


def prueba_pipeline_cubre_todos_los_tipos_de_senal_nlp() -> None:
    tipos_detectados = {
        anotacion.tipo_senal
        for nombre in NOMBRES_ERS
        for anotacion in _resultado(nombre).anotaciones
    }

    assert tipos_detectados == set(TipoSenalNLP)


@pytest.mark.parametrize("nombre", NOMBRES_ERS)
def prueba_anotaciones_son_trazables_al_fragmento(nombre: str) -> None:
    resultado = _resultado(nombre)
    fragmentos_por_id = {
        clasificado.fragmento.id: clasificado.fragmento
        for clasificado in resultado.fragmentos_clasificados
    }

    assert resultado.anotaciones
    for anotacion in resultado.anotaciones:
        fragmento = fragmentos_por_id[anotacion.fragmento_id]
        assert fragmento.texto[
            anotacion.posicion_inicio : anotacion.posicion_fin
        ] == anotacion.valor_detectado


def prueba_ers_incluyen_senales_de_calidad_documental() -> None:
    calidad_por_archivo = {
        nombre: {
            anotacion.tipo_senal
            for anotacion in _resultado(nombre).anotaciones
            if anotacion.tipo_senal
            in {TipoSenalNLP.TERMINO_VAGO, TipoSenalNLP.AMBIGUEDAD}
        }
        for nombre in NOMBRES_ERS
    }

    assert calidad_por_archivo["diagnostico_medico.txt"] == {
        TipoSenalNLP.TERMINO_VAGO
    }
    assert calidad_por_archivo["scoring_crediticio.txt"] == {
        TipoSenalNLP.TERMINO_VAGO
    }
    assert calidad_por_archivo["sistema_recomendador.txt"] == {
        TipoSenalNLP.TERMINO_VAGO,
        TipoSenalNLP.AMBIGUEDAD,
    }


def prueba_analizar_texto_equivale_al_pipeline_manual() -> None:
    documento = cargar_documento_desde_ruta(
        DIRECTORIO_ERS / "scoring_crediticio.txt"
    )
    texto = documento.contenido_extraido

    texto_normalizado = NormalizadorDeTexto().normalizar(texto)
    fragmentos = segmentar(texto_normalizado.normalizado)
    clasificaciones_esperadas = clasificar_fragmentos(fragmentos)
    anotaciones_esperadas = []
    for fragmento in fragmentos:
        anotaciones_esperadas.extend(extraer_de_fragmentos([fragmento]))
        anotaciones_esperadas.extend(detectar_en_fragmentos([fragmento]))

    obtenido = analizar_texto(texto)

    assert obtenido.texto_normalizado == texto_normalizado
    assert [r.clasificacion for r in obtenido.fragmentos_clasificados] == [
        r.clasificacion for r in clasificaciones_esperadas
    ]
    secuencia_obtenida_por_id = {
        r.fragmento.id: r.fragmento.secuencia_orden
        for r in obtenido.fragmentos_clasificados
    }
    secuencia_esperada_por_id = {
        fragmento.id: fragmento.secuencia_orden for fragmento in fragmentos
    }
    assert {
        (
            secuencia_obtenida_por_id[r.fragmento_id],
            r.tipo_senal,
            r.valor_detectado,
            r.posicion_inicio,
            r.posicion_fin,
        )
        for r in obtenido.anotaciones
    } == {
        (
            secuencia_esperada_por_id[r.fragmento_id],
            r.tipo_senal,
            r.valor_detectado,
            r.posicion_inicio,
            r.posicion_fin,
        )
        for r in anotaciones_esperadas
    }


def prueba_analizar_texto_rechaza_texto_vacio() -> None:
    with pytest.raises(TextoVacioError):
        analizar_texto("   \n\n   ")
