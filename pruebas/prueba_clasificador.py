from typing import Optional

from etica_ia_ers.dominio import (
    FragmentoDocumental,
    TipoClasificacionFragmento,
    TipoFragmento,
)
from etica_ia_ers.procesamiento_textual_y_nlp import (
    NormalizadorDeTexto,
    clasificar_fragmento,
    clasificar_fragmentos,
    segmentar,
)


def _fragmento(
    texto: str,
    *,
    tipo: TipoFragmento = TipoFragmento.PARRAFO,
    seccion: Optional[str] = None,
    orden: int = 1,
) -> FragmentoDocumental:
    return FragmentoDocumental(
        secuencia_orden=orden,
        tipo_fragmento=tipo,
        texto=texto,
        seccion_origen=seccion,
        posicion_inicio=0,
        posicion_fin=len(texto),
    )


def prueba_clasifica_requisito_funcional() -> None:
    resultado = clasificar_fragmento(
        _fragmento("El sistema deberá registrar cada decisión automatizada.")
    )

    assert resultado.clasificacion == (
        TipoClasificacionFragmento.REQUISITO_FUNCIONAL
    )
    assert "comportamiento requerido" in resultado.senales


def prueba_clasifica_requisito_no_funcional() -> None:
    resultado = clasificar_fragmento(
        _fragmento("El sistema deberá responder en menos de dos segundos.")
    )

    assert resultado.clasificacion == (
        TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL
    )
    assert "rendimiento" in resultado.senales


def prueba_clasifica_restriccion() -> None:
    resultado = clasificar_fragmento(
        _fragmento("El sistema no deberá utilizar datos biométricos.")
    )

    assert resultado.clasificacion == TipoClasificacionFragmento.RESTRICCION
    assert "prohibicion explicita" in resultado.senales


def prueba_clasifica_contexto() -> None:
    resultado = clasificar_fragmento(
        _fragmento("El propósito es asistir a profesionales de la salud.")
    )

    assert resultado.clasificacion == TipoClasificacionFragmento.CONTEXTO
    assert "proposito o alcance" in resultado.senales


def prueba_clasifica_como_otro_sin_senales_suficientes() -> None:
    resultado = clasificar_fragmento(_fragmento("Información complementaria."))

    assert resultado.clasificacion == TipoClasificacionFragmento.OTRO
    assert resultado.senales == ()


def prueba_reconoce_mayusculas_y_acentos() -> None:
    resultado = clasificar_fragmento(
        _fragmento("La APLICACIÓN deberá garantizar la CONFIDENCIALIDAD.")
    )

    assert resultado.clasificacion == (
        TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL
    )
    assert "seguridad o privacidad" in resultado.senales


def prueba_usa_seccion_como_senal_auxiliar() -> None:
    resultado = clasificar_fragmento(
        _fragmento(
            "Los datos se conservarán según lo definido.",
            seccion="4. Requisitos no funcionales",
        )
    )

    assert resultado.clasificacion == (
        TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL
    )
    assert "seccion de requisitos no funcionales" in resultado.senales


def prueba_senal_textual_prevalece_sobre_la_seccion() -> None:
    resultado = clasificar_fragmento(
        _fragmento(
            "El sistema no deberá compartir credenciales.",
            seccion="3. Requisitos funcionales",
        )
    )

    assert resultado.clasificacion == TipoClasificacionFragmento.RESTRICCION


def prueba_no_funcional_prevalece_sobre_funcional() -> None:
    resultado = clasificar_fragmento(
        _fragmento("El sistema deberá garantizar una disponibilidad del 99%.")
    )

    assert resultado.clasificacion == (
        TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL
    )


def prueba_encabezado_aislado_es_otro() -> None:
    resultado = clasificar_fragmento(
        _fragmento(
            "3. Requisitos no funcionales",
            tipo=TipoFragmento.ENCABEZADO,
        )
    )

    assert resultado.clasificacion == TipoClasificacionFragmento.OTRO
    assert resultado.senales == ("encabezado documental",)


def prueba_conserva_el_fragmento_original() -> None:
    fragmento = _fragmento(
        "El sistema deberá mostrar el resultado.",
        seccion="3. Requisitos funcionales",
    )
    resultado = clasificar_fragmento(fragmento)

    assert resultado.fragmento is fragmento
    assert resultado.fragmento.id == fragmento.id
    assert resultado.fragmento.texto == fragmento.texto
    assert resultado.fragmento.posicion_inicio == fragmento.posicion_inicio
    assert resultado.fragmento.posicion_fin == fragmento.posicion_fin


def prueba_clasificacion_por_lote_preserva_orden() -> None:
    fragmentos = [
        _fragmento("El sistema deberá registrar operaciones.", orden=1),
        _fragmento("El sistema no deberá revelar contraseñas.", orden=2),
        _fragmento("El objetivo es asistir al usuario.", orden=3),
    ]

    resultados = clasificar_fragmentos(fragmentos)

    assert [resultado.fragmento for resultado in resultados] == fragmentos
    assert [resultado.clasificacion for resultado in resultados] == [
        TipoClasificacionFragmento.REQUISITO_FUNCIONAL,
        TipoClasificacionFragmento.RESTRICCION,
        TipoClasificacionFragmento.CONTEXTO,
    ]


def prueba_integracion_normalizacion_segmentacion_clasificacion() -> None:
    texto = (
        "1. Objetivo\r\n\r\n"
        "El propósito es asistir al personal médico.\r\n\r\n"
        "2.1. El sistema deberá registrar las decisiones.\r\n\r\n"
        "2.2. El sistema deberá responder en menos de dos segundos."
    )
    normalizado = NormalizadorDeTexto().normalizar(texto)
    fragmentos = segmentar(normalizado.normalizado)

    resultados = clasificar_fragmentos(fragmentos)

    assert [resultado.clasificacion for resultado in resultados] == [
        TipoClasificacionFragmento.OTRO,
        TipoClasificacionFragmento.CONTEXTO,
        TipoClasificacionFragmento.REQUISITO_FUNCIONAL,
        TipoClasificacionFragmento.REQUISITO_NO_FUNCIONAL,
    ]
    assert [resultado.fragmento.secuencia_orden for resultado in resultados] == [
        1,
        2,
        3,
        4,
    ]
