from __future__ import annotations

from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    DimensionEtica,
    EstadoAplicacionGuardrail,
    NivelCobertura,
    SolicitudEvaluacionEtica,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_D01,
    GUARDRAILS_D02,
    GUARDRAILS_D01_D02,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto


def _evaluar_texto(texto: str, *guardrails):
    resultado_nlp = analizar_texto(texto)
    motor = MotorEvaluacionEtica(RepositorioGuardrailsEnMemoria(guardrails))
    resultado = motor.evaluar(
        SolicitudEvaluacionEtica(documento_id=uuid4(), resultado_nlp=resultado_nlp)
    )
    return resultado


def _hallazgo_de(resultado, codigo: str):
    for aplicacion in resultado.aplicaciones:
        if aplicacion.guardrail_codigo == codigo:
            return aplicacion
    raise AssertionError(f"No se encontro aplicacion para {codigo}")


def prueba_catalogo_no_tiene_codigos_duplicados() -> None:
    codigos = [g.definicion.codigo for g in GUARDRAILS_D01_D02]
    assert len(codigos) == len(set(codigos))


def prueba_catalogo_se_puede_cargar_en_repositorio() -> None:
    repositorio = RepositorioGuardrailsEnMemoria(GUARDRAILS_D01_D02)
    assert len(repositorio.listar()) == len(GUARDRAILS_D01_D02)


def prueba_guardrails_d01_estan_asociados_a_d01() -> None:
    for guardrail in GUARDRAILS_D01:
        assert DimensionEtica.D01 in guardrail.definicion.dimensiones


def prueba_guardrails_d02_estan_asociados_a_d02() -> None:
    for guardrail in GUARDRAILS_D02:
        assert DimensionEtica.D02 in guardrail.definicion.dimensiones


def prueba_todos_los_codigos_d01_d02_siguen_convencion_gr() -> None:
    for guardrail in GUARDRAILS_D01_D02:
        assert guardrail.definicion.codigo.startswith("GR-D01") or guardrail.definicion.codigo.startswith("GR-D02")


def prueba_ejemplo_proposito_generico_es_parcial() -> None:
    texto = "1.1. El sistema debera usar datos para una finalidad general de recomendacion."
    # evaluar usando el guardrail de presencia de proposito
    resultado = _evaluar_texto(texto, *GUARDRAILS_D01)

    aplicacion = _hallazgo_de(resultado, "GR-D01-PRES-PROPOSITO")
    assert aplicacion.estado == EstadoAplicacionGuardrail.APLICADO
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.PARCIAL


def prueba_texto_sin_mencion_de_proposito_es_ausente() -> None:
    texto = "1.1. El sistema debera procesar transacciones en menos de un segundo."
    resultado = _evaluar_texto(texto, *GUARDRAILS_D01)

    aplicacion = _hallazgo_de(resultado, "GR-D01-PRES-PROPOSITO")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


def prueba_ejemplo_proposito_explicito() -> None:
    texto = "1.2. El sistema debera cumplir el proposito del sistema de recomendar productos personalizados a usuarios registrados."
    resultado = _evaluar_texto(texto, *GUARDRAILS_D01)

    aplicacion = _hallazgo_de(resultado, "GR-D01-PRES-PROPOSITO")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_ejemplo_actores_presencia_e_impacto() -> None:
    texto = (
        "2.1. Actores afectados: usuarios finales, administradores y proveedores. "
        "Se realizo una evaluacion de impacto que identifica riesgos para usuarios." 
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D02)

    aplic_pres = _hallazgo_de(resultado, "GR-D02-PRES-ACTORES")
    aplic_impacto = _hallazgo_de(resultado, "GR-D02-VERIF-IMPACTOS")

    assert aplic_pres.hallazgo.nivel_preliminar in (NivelCobertura.PARCIAL, NivelCobertura.EXPLICITO)
    assert aplic_impacto.hallazgo.nivel_preliminar in (NivelCobertura.PARCIAL, NivelCobertura.EXPLICITO)


def prueba_catalogo_completo_sobre_documento_con_evidencia_mixta() -> None:
    texto = (
        "1.1. El sistema debera cumplir el proposito de recomendar productos.\n\n"
        "2.1. El sistema debera considerar actores: usuarios y socios.\n\n"
        "3.1. El sistema debera realizar una evaluacion de impacto para identificar efectos en usuarios."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D01_D02)

    assert len(resultado.aplicaciones) == len(GUARDRAILS_D01_D02)
    estados = {a.guardrail_codigo: a.estado for a in resultado.aplicaciones}
    assert all(estado == EstadoAplicacionGuardrail.APLICADO for estado in estados.values())


@pytest.mark.parametrize(
    "guardrail",
    GUARDRAILS_D01_D02,
    ids=[g.definicion.codigo for g in GUARDRAILS_D01_D02],
)
def prueba_cada_guardrail_produce_ausente_sobre_texto_neutro(guardrail) -> None:
    texto = "9.1. El sistema debera mostrar un mensaje de bienvenida al usuario."
    resultado = _evaluar_texto(texto, guardrail)

    aplicacion = resultado.aplicaciones[0]
    assert aplicacion.estado == EstadoAplicacionGuardrail.APLICADO
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
