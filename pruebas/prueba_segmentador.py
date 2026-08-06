from uuid import UUID

import pytest

from etica_ia_ers.dominio import FragmentoDocumental, TipoFragmento
from etica_ia_ers.procesamiento_textual_y_nlp import segmentar


def prueba_texto_vacio_lanza_error() -> None:
    with pytest.raises(ValueError):
        segmentar("")


def prueba_texto_solo_espacios_lanza_error() -> None:
    with pytest.raises(ValueError):
        segmentar("   \n\n   ")


def prueba_parrafo_simple() -> None:
    texto = "El sistema debe ser transparente en sus decisiones."
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert fragmentos[0].tipo_fragmento == TipoFragmento.PARRAFO
    assert fragmentos[0].texto == texto


def prueba_fragmentos_tienen_identificadores_unicos() -> None:
    fragmentos = segmentar("Primer parrafo.\n\nSegundo parrafo.")

    assert all(isinstance(fragmento.id, UUID) for fragmento in fragmentos)
    assert fragmentos[0].id != fragmentos[1].id


def prueba_encabezado_simple() -> None:
    texto = "3. Requisitos Específicos"
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert fragmentos[0].tipo_fragmento == TipoFragmento.ENCABEZADO
    assert fragmentos[0].identificador_ers == "3"


def prueba_encabezado_con_subnivel() -> None:
    texto = "3.1. Requisitos Funcionales"
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert fragmentos[0].tipo_fragmento == TipoFragmento.ENCABEZADO
    assert fragmentos[0].identificador_ers == "3.1"


def prueba_requisito_con_numeracion_compuesta() -> None:
    texto = "3.1.1. El sistema deberá proveer explicaciones comprensibles de sus decisiones automatizadas a los usuarios finales."
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert fragmentos[0].tipo_fragmento == TipoFragmento.REQUISITO
    assert fragmentos[0].identificador_ers == "3.1.1"


def prueba_requisito_normativo_de_primer_nivel() -> None:
    texto = "1. El sistema deberá registrar decisiones."
    fragmentos = segmentar(texto)

    assert fragmentos[0].tipo_fragmento == TipoFragmento.REQUISITO
    assert fragmentos[0].identificador_ers == "1"


def prueba_item_de_lista() -> None:
    texto = "- El nivel de detalle será configurable por el administrador."
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert fragmentos[0].tipo_fragmento == TipoFragmento.ITEM_LISTA
    assert fragmentos[0].identificador_ers is None



def prueba_documento_ers_completo() -> None:
    texto = (
        "3. Requisitos Específicos\n\n"
        "3.1. Requisitos Funcionales\n\n"
        "3.1.1. El sistema deberá proveer explicaciones comprensibles de sus decisiones.\n\n"
        "3.1.2. El sistema registrará cada decisión automatizada con su justificación.\n\n"
        "- El nivel de detalle será configurable.\n\n"
        "- Las explicaciones se generarán en tiempo real.\n\n"
        "El motor de IA utilizará modelos interpretables cuando sea posible."
    )
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 7

    assert fragmentos[0].tipo_fragmento == TipoFragmento.ENCABEZADO
    assert fragmentos[0].identificador_ers == "3"
    assert fragmentos[1].tipo_fragmento == TipoFragmento.ENCABEZADO
    assert fragmentos[1].identificador_ers == "3.1"

    assert fragmentos[2].tipo_fragmento == TipoFragmento.REQUISITO
    assert fragmentos[2].identificador_ers == "3.1.1"
    assert fragmentos[3].tipo_fragmento == TipoFragmento.REQUISITO
    assert fragmentos[3].identificador_ers == "3.1.2"

    assert fragmentos[4].tipo_fragmento == TipoFragmento.ITEM_LISTA
    assert fragmentos[5].tipo_fragmento == TipoFragmento.ITEM_LISTA

    assert fragmentos[6].tipo_fragmento == TipoFragmento.PARRAFO


def prueba_seccion_origen_se_propaga() -> None:
    texto = (
        "3. Requisitos\n\n"
        "3.1.1. El sistema será transparente.\n\n"
        "- Detalle adicional."
    )
    fragmentos = segmentar(texto)

    assert fragmentos[0].seccion_origen == "3. Requisitos"
    assert fragmentos[1].seccion_origen == "3. Requisitos"
    assert fragmentos[2].seccion_origen == "3. Requisitos"




def prueba_posiciones_son_correctas() -> None:
    texto = "3. Intro\n\nEl sistema debe cumplir."
    fragmentos = segmentar(texto)

    assert fragmentos[0].posicion_inicio == 0
    assert fragmentos[0].posicion_fin == 8
    assert fragmentos[1].posicion_inicio == 10
    assert texto[fragmentos[1].posicion_inicio:fragmentos[1].posicion_fin] == (
        "El sistema debe cumplir."
    )


def prueba_posiciones_delimitan_el_texto_del_fragmento() -> None:
    texto = "  Requisito trazable  \n  \n  Otro fragmento  "
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 2
    for fragmento in fragmentos:
        assert texto[
            fragmento.posicion_inicio:fragmento.posicion_fin
        ] == fragmento.texto


def prueba_orden_secuencial() -> None:
    texto = "A\n\nB\n\nC"
    fragmentos = segmentar(texto)

    assert [f.secuencia_orden for f in fragmentos] == [1, 2, 3]




def prueba_integracion_con_normalizador() -> None:
    from etica_ia_ers.procesamiento_textual_y_nlp import NormalizadorDeTexto

    texto_crudo = (
        "3. Requisitos\r\n"
        "\r\n"
        "3.1.1. El sistema deberá ser transparente.\r\n"
        "\r\n"
        "3.1.2. El sistema registrará decisiones.\r\n"
        "\r\n"
        "• Detalle del requisito."
    )
    normalizador = NormalizadorDeTexto()
    resultado = normalizador.normalizar(texto_crudo)
    fragmentos = segmentar(resultado.normalizado)

    assert fragmentos[0].tipo_fragmento == TipoFragmento.ENCABEZADO
    assert any(
        f.tipo_fragmento == TipoFragmento.REQUISITO for f in fragmentos
    )




def prueba_texto_sin_estructura_es_parrafo() -> None:
    texto = "Este es un texto libre sin ninguna estructura de ERS."
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert fragmentos[0].tipo_fragmento == TipoFragmento.PARRAFO


def prueba_multiples_items_lista_separados() -> None:
    texto = "- Primero\n\n- Segundo\n\n- Tercero"
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 3
    assert all(f.tipo_fragmento == TipoFragmento.ITEM_LISTA for f in fragmentos)


def prueba_requisitos_consecutivos_sin_lineas_vacias() -> None:
    texto = (
        "3.1.1. El sistema deberá registrar decisiones.\n"
        "3.1.2. El sistema deberá explicar resultados."
    )
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 2
    assert [fragmento.identificador_ers for fragmento in fragmentos] == [
        "3.1.1",
        "3.1.2",
    ]


def prueba_items_consecutivos_sin_lineas_vacias() -> None:
    fragmentos = segmentar("- Primero\n- Segundo\n- Tercero")

    assert len(fragmentos) == 3
    assert all(
        fragmento.tipo_fragmento == TipoFragmento.ITEM_LISTA
        for fragmento in fragmentos
    )


def prueba_requisito_multilinea() -> None:
    texto = (
        "3.1.1. El sistema deberá proveer explicaciones\n"
        "comprensibles de sus decisiones automatizadas\n"
        "a los usuarios finales del sistema."
    )
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert fragmentos[0].tipo_fragmento == TipoFragmento.REQUISITO
    assert "usuarios finales" in fragmentos[0].texto


def prueba_detecta_ambiguedades_y_terminos_vagos() -> None:
    texto = (
        "El sistema debe ser adecuado y, según corresponda, "
        "proporcionar explicaciones comprensibles."
    )
    fragmentos = segmentar(texto)

    assert len(fragmentos) == 1
    assert "adecuado" in fragmentos[0].terminos_vagos
    assert "según corresponda" in fragmentos[0].ambiguedades
