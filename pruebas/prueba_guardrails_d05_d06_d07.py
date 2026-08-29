"""Tests de los guardrails conceptuales de transparencia, explicabilidad y
supervision humana.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    DimensionEtica,
    NivelCobertura,
    SolicitudEvaluacionEtica,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_D05,
    GUARDRAILS_D05_D07,
    GUARDRAILS_D06,
    GUARDRAILS_D07,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto


def _evaluar_texto(texto: str, *guardrails):
    resultado = analizar_texto(texto)
    motor = MotorEvaluacionEtica(RepositorioGuardrailsEnMemoria(guardrails))
    return motor.evaluar(
        SolicitudEvaluacionEtica(documento_id=uuid4(), resultado_nlp=resultado)
    )


def _nivel(resultado, codigo: str) -> NivelCobertura:
    for aplicacion in resultado.aplicaciones:
        if aplicacion.guardrail_codigo == codigo:
            assert aplicacion.hallazgo is not None
            return aplicacion.hallazgo.nivel_preliminar
    raise AssertionError(f"No se encontro aplicacion para {codigo}")


def prueba_catalogo_d05_d07_tiene_23_guardrails_sin_duplicados() -> None:
    codigos = [guardrail.definicion.codigo for guardrail in GUARDRAILS_D05_D07]
    assert len(codigos) == 23
    assert len(codigos) == len(set(codigos))


@pytest.mark.parametrize(
    ("catalogo", "dimension"),
    (
        (GUARDRAILS_D05, DimensionEtica.D05),
        (GUARDRAILS_D06, DimensionEtica.D06),
        (GUARDRAILS_D07, DimensionEtica.D07),
    ),
)
def prueba_catalogos_estan_asociados_a_su_dimension(catalogo, dimension) -> None:
    assert all(dimension in guardrail.definicion.dimensiones for guardrail in catalogo)


def prueba_transparencia_generica_es_parcial() -> None:
    resultado = _evaluar_texto(
        "1.1. El sistema debera ser transparente para los usuarios.",
        GUARDRAILS_D05[0],
    )
    assert _nivel(resultado, "GR-D05-PRES-IA") == NivelCobertura.PARCIAL


def prueba_transparencia_con_ia_destinatario_canal_y_limites_es_explicita() -> None:
    texto = (
        "1.1. El sistema debera informar al usuario que la recomendacion fue "
        "generada por IA antes de confirmar la accion, mediante una pantalla "
        "de informacion, incluyendo sus limites."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D05)
    assert _nivel(resultado, "GR-D05-PRES-IA") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D05-DELIM-DESTINATARIOS") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D05-VERIF-CANAL") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D05-VERIF-LIMITES") == NivelCobertura.EXPLICITO


def prueba_explicabilidad_declarativa_es_parcial() -> None:
    resultado = _evaluar_texto(
        "2.1. El sistema debera proporcionar explicaciones adecuadas para las recomendaciones.",
        GUARDRAILS_D06[0],
    )
    assert _nivel(resultado, "GR-D06-PRES-EXPLICACION") == NivelCobertura.PARCIAL


def prueba_explicabilidad_con_factores_para_analista_es_explicita() -> None:
    texto = (
        "2.1. Ante una decision de rechazo, el sistema debera proporcionar "
        "una explicacion para el operador en formato de texto con los tres "
        "factores principales considerados y usar la explicacion para la revision."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D06)
    assert _nivel(resultado, "GR-D06-PRES-EXPLICACION") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D06-VERIF-FORMATO") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D06-CTRL-REVISION") == NivelCobertura.EXPLICITO


def prueba_supervision_humana_generica_es_parcial() -> None:
    resultado = _evaluar_texto(
        "3.1. Las decisiones podran ser revisadas por personal autorizado.",
        GUARDRAILS_D07[0],
    )
    assert _nivel(resultado, "GR-D07-PRES-HUMANO") == NivelCobertura.PARCIAL


def prueba_supervision_con_autoridad_condicion_procedimiento_y_registro_es_explicita() -> None:
    texto = (
        "3.1. Toda recomendacion de alto riesgo debera ser revisada por un "
        "supervisor autorizado, quien podra aprobarla, rechazarla o escalarla "
        "siguiendo el procedimiento de revision y registrando motivo y decision."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D07)
    assert _nivel(resultado, "GR-D07-PRES-HUMANO") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D07-DELIM-ROLES") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D07-CTRL-INTERVENCION") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D07-VERIF-PROCEDIMIENTO") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D07-RESP-REGISTRO") == NivelCobertura.EXPLICITO


@pytest.mark.parametrize(
    "guardrail",
    GUARDRAILS_D05_D07,
    ids=[guardrail.definicion.codigo for guardrail in GUARDRAILS_D05_D07],
)
def prueba_guardrails_sin_evidencia_son_ausentes(guardrail) -> None:
    resultado = _evaluar_texto(
        "9.1. El sistema debera mostrar un mensaje de bienvenida.",
        guardrail,
    )
    assert _nivel(resultado, guardrail.definicion.codigo) == NivelCobertura.AUSENTE
