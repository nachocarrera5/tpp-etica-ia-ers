from typing import List, Optional

import pytest

from etica_ia_ers.dominio import (
    AnotacionNLP,
    FragmentoDocumental,
    TipoFragmento,
    TipoSenalNLP,
)
from etica_ia_ers.procesamiento_textual_y_nlp import (
    ModeloNLPNoDisponibleError,
    NormalizadorDeTexto,
    clasificar_fragmentos,
    extraer_actores_acciones_condiciones,
    extraer_de_fragmentos,
    segmentar,
)


def _fragmento(
    texto: str,
    *,
    tipo: TipoFragmento = TipoFragmento.REQUISITO,
    orden: int = 1,
) -> FragmentoDocumental:
    return FragmentoDocumental(
        secuencia_orden=orden,
        tipo_fragmento=tipo,
        texto=texto,
        posicion_inicio=0,
        posicion_fin=len(texto),
    )


def _filtrar(
    anotaciones: List[AnotacionNLP],
    tipo: TipoSenalNLP,
) -> List[AnotacionNLP]:
    return [item for item in anotaciones if item.tipo_senal == tipo]


def _buscar(
    anotaciones: List[AnotacionNLP],
    tipo: TipoSenalNLP,
    valor: str,
) -> Optional[AnotacionNLP]:
    return next(
        (
            item
            for item in anotaciones
            if item.tipo_senal == tipo and item.valor_detectado == valor
        ),
        None,
    )


def prueba_extrae_sujeto_accion_destinatario_y_condicion() -> None:
    fragmento = _fragmento(
        "El sistema deberá informar al usuario los factores principales "
        "cuando rechace una solicitud."
    )

    anotaciones = extraer_actores_acciones_condiciones(fragmento)

    sistema = _buscar(anotaciones, TipoSenalNLP.ACTOR, "El sistema")
    usuario = _buscar(anotaciones, TipoSenalNLP.ACTOR, "usuario")
    accion = _buscar(
        anotaciones,
        TipoSenalNLP.ACCION,
        "deberá informar al usuario los factores principales",
    )
    condicion = _buscar(
        anotaciones,
        TipoSenalNLP.CONDICION,
        "cuando rechace una solicitud",
    )

    assert sistema is not None and sistema.metadatos["rol"] == "sujeto"
    assert usuario is not None and usuario.metadatos["rol"] == "destinatario"
    assert accion is not None and accion.metadatos["lema"] == "informar"
    assert condicion is not None
    assert condicion.metadatos["tipo_condicion"] == "temporal"


def prueba_extrae_acciones_coordinadas() -> None:
    fragmento = _fragmento(
        "El supervisor deberá revisar y aprobar la recomendación."
    )

    anotaciones = extraer_actores_acciones_condiciones(fragmento)
    acciones = _filtrar(anotaciones, TipoSenalNLP.ACCION)

    assert [accion.metadatos["lema"] for accion in acciones] == [
        "revisar",
        "aprobar",
    ]


def prueba_extrae_agente_en_voz_pasiva() -> None:
    fragmento = _fragmento(
        "Las decisiones serán revisadas por un supervisor autorizado."
    )

    anotaciones = extraer_actores_acciones_condiciones(fragmento)
    supervisor = _buscar(
        anotaciones,
        TipoSenalNLP.ACTOR,
        "un supervisor autorizado",
    )

    assert supervisor is not None
    assert supervisor.metadatos["rol"] == "agente_pasivo"


def prueba_distingue_actor_afectado_en_voz_pasiva() -> None:
    fragmento = _fragmento(
        "Los usuarios serán notificados por el sistema."
    )

    anotaciones = extraer_actores_acciones_condiciones(fragmento)
    usuarios = _buscar(anotaciones, TipoSenalNLP.ACTOR, "Los usuarios")
    sistema = _buscar(anotaciones, TipoSenalNLP.ACTOR, "el sistema")

    assert usuarios is not None and usuarios.metadatos["rol"] == "afectado"
    assert sistema is not None and sistema.metadatos["rol"] == "agente_pasivo"


def prueba_extrae_condicion_al_inicio() -> None:
    fragmento = _fragmento(
        "Cuando el nivel de confianza sea bajo, el supervisor deberá revisar."
    )

    condiciones = _filtrar(
        extraer_actores_acciones_condiciones(fragmento),
        TipoSenalNLP.CONDICION,
    )

    assert [item.valor_detectado for item in condiciones] == [
        "Cuando el nivel de confianza sea bajo"
    ]


def prueba_extrae_condicion_temporal_con_acento() -> None:
    fragmento = _fragmento(
        "El sistema eliminará los datos después de finalizar el análisis."
    )

    condiciones = _filtrar(
        extraer_actores_acciones_condiciones(fragmento),
        TipoSenalNLP.CONDICION,
    )

    assert [item.valor_detectado for item in condiciones] == [
        "después de finalizar el análisis"
    ]


def prueba_no_inventa_actor_cuando_no_esta_explicitado() -> None:
    fragmento = _fragmento("Se registrará la decisión automatizada.")

    anotaciones = extraer_actores_acciones_condiciones(fragmento)

    assert _filtrar(anotaciones, TipoSenalNLP.ACTOR) == []
    assert _filtrar(anotaciones, TipoSenalNLP.ACCION)


def prueba_offsets_reconstruyen_todos_los_valores() -> None:
    fragmento = _fragmento(
        "Ante un error, el operador deberá notificar al administrador."
    )

    anotaciones = extraer_actores_acciones_condiciones(fragmento)

    assert anotaciones
    for anotacion in anotaciones:
        assert fragmento.texto[
            anotacion.posicion_inicio:anotacion.posicion_fin
        ] == anotacion.valor_detectado


def prueba_elimina_anotaciones_duplicadas() -> None:
    fragmento = _fragmento(
        "El supervisor deberá registrar la aprobación."
    )

    anotaciones = extraer_actores_acciones_condiciones(fragmento)
    claves = {
        (item.tipo_senal, item.posicion_inicio, item.posicion_fin)
        for item in anotaciones
    }

    assert len(claves) == len(anotaciones)


def prueba_omite_encabezados() -> None:
    fragmento = _fragmento(
        "3. Actores y responsables",
        tipo=TipoFragmento.ENCABEZADO,
    )

    assert extraer_actores_acciones_condiciones(fragmento) == []


def prueba_metadatos_identifican_procesador_y_modelo() -> None:
    anotaciones = extraer_actores_acciones_condiciones(
        _fragmento("El sistema deberá registrar la decisión.")
    )

    assert anotaciones
    for anotacion in anotaciones:
        assert anotacion.confianza is None
        assert anotacion.metadatos["procesador"] == "spacy_reglas"
        assert anotacion.metadatos["version_herramienta"] == "3.8.7"
        assert anotacion.metadatos["modelo"] == "es_core_news_sm"
        assert anotacion.metadatos["version_modelo"] == "3.8.0"


def prueba_extraccion_por_lote_preserva_orden_documental() -> None:
    fragmentos = [
        _fragmento("El sistema registrará la solicitud.", orden=1),
        _fragmento("El operador revisará el resultado.", orden=2),
    ]

    anotaciones = extraer_de_fragmentos(fragmentos)
    posiciones_documentos = [
        next(
            indice
            for indice, fragmento in enumerate(fragmentos)
            if fragmento.id == anotacion.fragmento_id
        )
        for anotacion in anotaciones
    ]

    assert posiciones_documentos == sorted(posiciones_documentos)


def prueba_error_claro_si_el_modelo_no_esta_disponible(monkeypatch) -> None:
    from etica_ia_ers.procesamiento_textual_y_nlp import extractor_elementos

    def fallar_importacion():
        raise ImportError("modelo ausente")

    extractor_elementos._cargar_modelo.cache_clear()
    monkeypatch.setattr(
        extractor_elementos,
        "_importar_modelo",
        fallar_importacion,
    )

    with pytest.raises(ModeloNLPNoDisponibleError):
        extractor_elementos._cargar_modelo()


def prueba_integracion_del_flujo_nlp() -> None:
    texto = (
        "1. Requisitos\r\n\r\n"
        "1.1. El sistema deberá informar al usuario cuando rechace "
        "una solicitud.\r\n\r\n"
        "1.2. El supervisor deberá revisar la decisión."
    )
    normalizado = NormalizadorDeTexto().normalizar(texto)
    fragmentos = segmentar(normalizado.normalizado)
    clasificados = clasificar_fragmentos(fragmentos)

    anotaciones = extraer_de_fragmentos(
        resultado.fragmento for resultado in clasificados
    )

    assert any(item.tipo_senal == TipoSenalNLP.ACTOR for item in anotaciones)
    assert any(item.tipo_senal == TipoSenalNLP.ACCION for item in anotaciones)
    assert any(item.tipo_senal == TipoSenalNLP.CONDICION for item in anotaciones)
