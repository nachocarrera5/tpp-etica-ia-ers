from uuid import UUID

import pytest

from etica_ia_ers.dominio import (
    FragmentoDocumental,
    TipoFragmento,
    TipoSenalNLP,
)
from etica_ia_ers.procesamiento_textual_y_nlp import (
    detectar_ambiguedades_y_terminos_vagos,
    detectar_en_fragmentos,
    segmentar,
)


def _fragmento(
    texto: str,
    tipo: TipoFragmento = TipoFragmento.REQUISITO,
    secuencia: int = 1,
) -> FragmentoDocumental:
    return FragmentoDocumental(
        secuencia_orden=secuencia,
        tipo_fragmento=tipo,
        texto=texto,
    )


def prueba_detecta_termino_vago_y_ambiguedad() -> None:
    fragmento = _fragmento(
        "El sistema debe ser adecuado y, según corresponda, informar al usuario."
    )

    anotaciones = detectar_ambiguedades_y_terminos_vagos(fragmento)

    assert [(item.tipo_senal, item.valor_detectado) for item in anotaciones] == [
        (TipoSenalNLP.TERMINO_VAGO, "adecuado"),
        (TipoSenalNLP.AMBIGUEDAD, "según corresponda"),
    ]


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("La respuesta debe ser BÁSICA.", "BÁSICA"),
        ("Las medidas deben ser apropiadas.", "apropiadas"),
        ("El reporte debe ser útil.", "útil"),
        ("Los resultados deben ser útiles.", "útiles"),
        ("El rendimiento debe ser optimo.", "optimo"),
    ],
)
def prueba_reconoce_mayusculas_acentos_genero_y_numero(
    texto: str, esperado: str
) -> None:
    anotaciones = detectar_ambiguedades_y_terminos_vagos(_fragmento(texto))

    assert [item.valor_detectado for item in anotaciones] == [esperado]


@pytest.mark.parametrize(
    "texto",
    [
        "El sistema debe utilizar datos personales.",
        "El proceso debe completarse sin errores.",
        "La aplicación optimiza el resultado.",
    ],
)
def prueba_no_detecta_subcadenas_como_terminos_vagos(texto: str) -> None:
    assert detectar_ambiguedades_y_terminos_vagos(_fragmento(texto)) == []


def prueba_conserva_offsets_y_texto_originales() -> None:
    fragmento = _fragmento(
        "Cuando corresponda, debe responder en la medida de lo posible."
    )

    [anotacion] = detectar_ambiguedades_y_terminos_vagos(fragmento)

    assert isinstance(anotacion.id, UUID)
    assert anotacion.fragmento_id == fragmento.id
    assert fragmento.texto[
        anotacion.posicion_inicio : anotacion.posicion_fin
    ] == anotacion.valor_detectado
    assert anotacion.valor_detectado == "en la medida de lo posible"


def prueba_registra_regla_y_metodo_sin_inventar_confianza() -> None:
    [anotacion] = detectar_ambiguedades_y_terminos_vagos(
        _fragmento("El resultado debe ser razonable.")
    )

    assert anotacion.confianza is None
    assert anotacion.metadatos == {
        "regla": "termino_vago_razonable",
        "metodo": "patron_lexico",
    }


def prueba_conserva_ocurrencias_repetidas_con_rangos_distintos() -> None:
    fragmento = _fragmento("Debe ser adecuado, pero realmente adecuado.")

    anotaciones = detectar_ambiguedades_y_terminos_vagos(fragmento)

    assert [item.valor_detectado for item in anotaciones] == [
        "adecuado",
        "adecuado",
    ]
    assert anotaciones[0].posicion_inicio != anotaciones[1].posicion_inicio


def prueba_omite_encabezados_aislados() -> None:
    fragmento = _fragmento("Criterio adecuado", TipoFragmento.ENCABEZADO)

    assert detectar_ambiguedades_y_terminos_vagos(fragmento) == []


def prueba_lote_preserva_orden_documental() -> None:
    fragmentos = [
        _fragmento("Debe ser suficiente.", secuencia=1),
        _fragmento("Debe ser eficiente.", secuencia=2),
    ]

    anotaciones = detectar_en_fragmentos(fragmentos)

    assert [item.fragmento_id for item in anotaciones] == [
        fragmentos[0].id,
        fragmentos[1].id,
    ]


def prueba_integracion_segmentacion_y_deteccion() -> None:
    fragmentos = segmentar(
        "1. Requisitos\n\n"
        "1.1. El sistema debe responder de forma eficiente.\n\n"
        "1.2. Según sea necesario, debe notificar al usuario."
    )

    anotaciones = detectar_en_fragmentos(fragmentos)

    assert [item.tipo_senal for item in anotaciones] == [
        TipoSenalNLP.TERMINO_VAGO,
        TipoSenalNLP.AMBIGUEDAD,
    ]
    assert [item.valor_detectado for item in anotaciones] == [
        "eficiente",
        "Según sea necesario",
    ]
