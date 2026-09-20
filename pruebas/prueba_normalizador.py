"""Tests para el módulo de normalización de texto de documentos ERS."""

import pytest

from etica_ia_ers.procesamiento_textual_y_nlp import (
    ErrorEnPasoDeNormalizacion,
    NormalizadorDeTexto,
    PasoDesconocidoError,
    TextoVacioError,
)
from etica_ia_ers.procesamiento_textual_y_nlp.normalizador import (
    colapsar_espacios,
    colapsar_lineas_en_blanco,
    eliminar_boilerplate_repetido,
    eliminar_caracteres_de_control,
    eliminar_marcadores_de_pagina,
    normalizar_comillas,
    normalizar_guiones,
    normalizar_numeracion,
    normalizar_saltos_de_linea,
    normalizar_unicode,
    normalizar_vinetas,
    PasoNormalizacion,
    PASOS_POR_DEFECTO,
)
from etica_ia_ers.dominio import TextoNormalizado


def prueba_normalizar_unicode_unifica_formas() -> None:
    assert normalizar_unicode("cafe\u0301") == "caf\u00e9"
    assert normalizar_unicode("n\u0303") == "\u00f1"
    assert normalizar_unicode("texto ASCII") == "texto ASCII"


def prueba_eliminar_caracteres_de_control() -> None:
    assert eliminar_caracteres_de_control("a\x00b\x07c\x0cd") == "abcd"
    assert eliminar_caracteres_de_control("linea\ntab\t") == "linea\ntab\t"


def prueba_normalizar_saltos_de_linea() -> None:
    assert normalizar_saltos_de_linea("a\r\nb\rc") == "a\nb\nc"
    assert normalizar_saltos_de_linea("a\n\n\n\nb") == "a\n\nb"
    assert normalizar_saltos_de_linea("a\n\nb") == "a\n\nb"


def prueba_normalizar_comillas() -> None:
    assert normalizar_comillas("\u201cHola\u201d") == '"Hola"'
    assert normalizar_comillas("\u2018it\u2019s") == "'it's"
    assert normalizar_comillas("\u00abcita\u00bb") == '"cita"'
    assert normalizar_comillas('"recta"') == '"recta"'


def prueba_normalizar_guiones() -> None:
    assert normalizar_guiones("a\u2014b\u2013c") == "a-b-c"
    assert normalizar_guiones("sub-item") == "sub-item"


def prueba_normalizar_vinetas() -> None:
    assert normalizar_vinetas("• Primero\n● Segundo\n◦ Tercero") == (
        "- Primero\n- Segundo\n- Tercero"
    )
    assert normalizar_vinetas("   ▪ Indentado") == "- Indentado"
    assert normalizar_vinetas("símbolo • aquí") == "símbolo • aquí"


def prueba_eliminar_marcadores_de_pagina() -> None:
    texto = "Contenido\nPágina 5 de 20\nMás\n\n42\n\nFin"
    resultado = eliminar_marcadores_de_pagina(texto)
    assert "Página 5 de 20" not in resultado
    assert "42" in resultado
    assert "Contenido" in resultado and "Fin" in resultado
    assert eliminar_marcadores_de_pagina("requisito 42 dice") == "requisito 42 dice"
    assert "12345" in eliminar_marcadores_de_pagina("x\n12345\ny")


def prueba_pipeline_preserva_valores_numericos_en_lineas_separadas() -> None:
    texto = (
        "Cantidad maxima de reintentos\n\n"
        "3\n\n"
        "El sistema debera bloquear nuevos intentos."
    )

    resultado = NormalizadorDeTexto().normalizar(texto)

    assert "\n\n3\n\n" in resultado.normalizado


def prueba_normalizar_numeracion() -> None:
    assert normalizar_numeracion("1) Requisito") == "1. Requisito"
    assert normalizar_numeracion("3.1) Sub") == "3.1. Sub"
    assert normalizar_numeracion("3.1.2- Item") == "3.1.2. Item"
    assert normalizar_numeracion("3.1. Ya ok") == "3.1. Ya ok"
    assert normalizar_numeracion("entre 1-5 opciones") == "entre 1-5 opciones"


def prueba_colapsar_espacios() -> None:
    assert colapsar_espacios("a   b\t\tc") == "a b c"
    assert colapsar_espacios("  inicio  \n  fin  ") == "inicio\nfin"


def prueba_colapsar_lineas_en_blanco() -> None:
    assert colapsar_lineas_en_blanco("a\n\n\n\nb") == "a\n\nb"
    assert colapsar_lineas_en_blanco("a\n   \n   \nb") == "a\n\nb"
    assert colapsar_lineas_en_blanco("a\n\nb") == "a\n\nb"


def prueba_eliminar_boilerplate_repetido_quita_pie_de_pagina_administrativo() -> None:
    pie_de_pagina = (
        "Esta es una copia autentica imprimible de un documento electronico "
        "administrativo archivado por la Comunidad Autonoma de Murcia."
    )
    texto = (
        "1. Objetivo\n"
        f"{pie_de_pagina}\n"
        "El sistema debera clasificar el riesgo del solicitante.\n"
        f"{pie_de_pagina}\n"
        "2. Alcance\n"
        f"{pie_de_pagina}\n"
        "El sistema opera unicamente sobre datos financieros.\n"
    )
    resultado = eliminar_boilerplate_repetido(texto)
    assert pie_de_pagina not in resultado
    assert "1. Objetivo" in resultado
    assert "clasificar el riesgo" in resultado
    assert "2. Alcance" in resultado
    assert "datos financieros" in resultado


def prueba_eliminar_boilerplate_repetido_preserva_lineas_no_repetidas() -> None:
    texto = "Requisito unico bastante largo que no se repite en el documento."
    assert eliminar_boilerplate_repetido(texto) == texto


def prueba_eliminar_boilerplate_repetido_no_afecta_lineas_cortas_repetidas() -> None:
    texto = "- Si\n- Si\n- Si\n- Si\n"
    assert eliminar_boilerplate_repetido(texto) == texto


def prueba_eliminar_boilerplate_repetido_preserva_requisitos_repetidos() -> None:
    requisito = (
        "El sistema debera conservar un registro integro de cada decision "
        "automatizada para permitir su auditoria."
    )
    texto = "\n".join((requisito, requisito, requisito))
    assert eliminar_boilerplate_repetido(texto) == texto


def prueba_pipeline_completo_elimina_boilerplate_de_pdf_administrativo() -> None:
    pie_de_pagina = (
        "GAMBIN MARIN, MIGUEL ANGEL 18/02/2026 Esta es una copia autentica "
        "imprimible de un documento electronico administrativo archivado."
    )
    texto = (
        "3.1. El sistema debera responder cada consulta en menos de tres "
        f"segundos.\n{pie_de_pagina}\n\n"
        f"3.2. El sistema debera cifrar los datos.\n{pie_de_pagina}\n\n"
        f"3.3. Otro requisito cualquiera.\n{pie_de_pagina}\n"
    )
    resultado = NormalizadorDeTexto().normalizar(texto)
    assert pie_de_pagina not in resultado.normalizado
    assert "responder cada consulta" in resultado.normalizado
    assert "cifrar los datos" in resultado.normalizado


def prueba_pipeline_devuelve_texto_normalizado_con_trazabilidad() -> None:
    normalizador = NormalizadorDeTexto()
    resultado = normalizador.normalizar("Texto válido.")

    assert isinstance(resultado, TextoNormalizado)
    assert resultado.original == "Texto válido."
    assert resultado.normalizado == "Texto válido."
    assert len(resultado.pasos_aplicados) == len(PASOS_POR_DEFECTO)


def prueba_pipeline_preserva_capitalizacion() -> None:
    normalizador = NormalizadorDeTexto()
    resultado = normalizador.normalizar("El sistema de IA cumple GDPR y la ERS.")
    assert "IA" in resultado.normalizado
    assert "GDPR" in resultado.normalizado
    assert "ERS" in resultado.normalizado


def prueba_pipeline_documento_ers_completo() -> None:
    ers = (
        "3. Requisitos Específicos\r\n"
        "\r\n"
        "3.1) El sistema de IA deberá proveer explicaciones.\r\n"
        "\r\n"
        "• El nivel de detalle será \u201cconfigurable\u201d.\r\n"
        "● Las explicaciones se generarán en tiempo real.\r\n"
        "\r\n"
        "Página 15 de 42\r\n"
        "\r\n"
        "3.2) El sistema implementará auditoría.\r\n"
    )
    resultado = NormalizadorDeTexto().normalizar(ers)

    assert "3. Requisitos Específicos" in resultado.normalizado
    assert "3.1. El sistema de IA" in resultado.normalizado
    assert "3.2. El sistema implementará" in resultado.normalizado
    assert "- El nivel de detalle" in resultado.normalizado
    assert "- Las explicaciones" in resultado.normalizado
    assert "Página 15 de 42" not in resultado.normalizado
    assert "\r" not in resultado.normalizado
    assert '"configurable"' in resultado.normalizado


def prueba_pipeline_idempotencia() -> None:
    texto = "• Requisito\r\n\u201cEl sistema\u201d\r\n\r\n\r\nPágina 1 de 5\r\n"
    normalizador = NormalizadorDeTexto()
    primera = normalizador.normalizar(texto)
    segunda = normalizador.normalizar(primera.normalizado)
    assert primera.normalizado == segunda.normalizado



def prueba_con_pasos_aplica_solo_seleccionados() -> None:
    normalizador = NormalizadorDeTexto.con_pasos(["colapsar_espacios"])
    resultado = normalizador.normalizar("  a   b  ")
    assert resultado.normalizado == "a b"
    assert resultado.pasos_aplicados == ["colapsar_espacios"]


def prueba_sin_pasos_excluye_correctamente() -> None:
    normalizador = NormalizadorDeTexto.sin_pasos(
        ["eliminar_marcadores_de_pagina"]
    )
    resultado = normalizador.normalizar("Texto\n\n5\n\nMás")
    assert "5" in resultado.normalizado


def prueba_sin_ningun_paso_no_modifica() -> None:
    normalizador = NormalizadorDeTexto(pasos=[])
    resultado = normalizador.normalizar("  texto  \r\n")
    assert resultado.normalizado == "  texto  \r\n"
    assert resultado.pasos_aplicados == []


def prueba_texto_vacio_lanza_error() -> None:
    normalizador = NormalizadorDeTexto()
    with pytest.raises(TextoVacioError):
        normalizador.normalizar("")


@pytest.mark.parametrize("texto", ["   ", "\t\t", "\n\n", "  \r\n\t  "])
def prueba_texto_solo_whitespace_lanza_error(texto: str) -> None:
    with pytest.raises(TextoVacioError):
        NormalizadorDeTexto().normalizar(texto)


def prueba_paso_desconocido_lanza_error() -> None:
    with pytest.raises(PasoDesconocidoError, match="inexistente"):
        NormalizadorDeTexto.con_pasos(["inexistente"])


def prueba_error_en_paso_se_envuelve() -> None:
    def paso_roto(texto: str) -> str:
        raise RuntimeError("boom")

    normalizador = NormalizadorDeTexto(
        pasos=[PasoNormalizacion("roto", paso_roto)]
    )
    with pytest.raises(ErrorEnPasoDeNormalizacion) as exc_info:
        normalizador.normalizar("texto válido")

    assert exc_info.value.nombre_paso == "roto"
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def prueba_errores_heredan_de_clase_base() -> None:
    from etica_ia_ers.procesamiento_textual_y_nlp import ErrorNormalizacion

    assert issubclass(TextoVacioError, ErrorNormalizacion)
    assert issubclass(PasoDesconocidoError, ErrorNormalizacion)
    assert issubclass(ErrorEnPasoDeNormalizacion, ErrorNormalizacion)
