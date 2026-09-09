"""Tests de los guardrails conceptuales de transparencia, explicabilidad y
supervision humana.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    DimensionEtica,
    FamiliaGuardrail,
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
from etica_ia_ers.rubrica_y_agregacion import calcular_cobertura_etica


_CODIGOS_ESPERADOS = (
    "GR-D05-PRES-IA",
    "GR-D05-DELIM-DESTINATARIOS",
    "GR-D05-DELIM-CONTENIDO",
    "GR-D05-VERIF-CANAL",
    "GR-D05-VERIF-LIMITES",
    "GR-D05-RESP-ACTUALIZACION",
    "GR-D05-QUAL-DECLARATIVO",
    "GR-D06-PRES-EXPLICACION",
    "GR-D06-DELIM-SALIDAS",
    "GR-D06-DELIM-DESTINATARIOS",
    "GR-D06-VERIF-FORMATO",
    "GR-D06-VERIF-UTILIDAD",
    "GR-D06-CTRL-REVISION",
    "GR-D06-RESP-EXPLICACION",
    "GR-D06-QUAL-DECLARATIVO",
    "GR-D07-PRES-HUMANO",
    "GR-D07-DELIM-DECISIONES",
    "GR-D07-DELIM-ROLES",
    "GR-D07-CTRL-INTERVENCION",
    "GR-D07-VERIF-ACTIVACION",
    "GR-D07-VERIF-PROCEDIMIENTO",
    "GR-D07-RESP-REGISTRO",
    "GR-D07-QUAL-DECLARATIVO",
)


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
    assert tuple(codigos) == _CODIGOS_ESPERADOS
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


def prueba_catalogo_cubre_las_seis_familias_y_declara_criterios() -> None:
    familias = {
        guardrail.definicion.familia for guardrail in GUARDRAILS_D05_D07
    }
    assert familias == set(FamiliaGuardrail)
    assert all(
        guardrail.definicion.criterios
        for guardrail in GUARDRAILS_D05_D07
    )


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
    assert _nivel(
        resultado,
        "GR-D05-DELIM-DESTINATARIOS",
    ) == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D05-VERIF-CANAL") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D05-VERIF-LIMITES") == NivelCobertura.EXPLICITO


def prueba_comunicacion_tecnica_entre_sistemas_no_es_explicita() -> None:
    texto = (
        "1.1. El sistema de IA debera informar mediante una notificacion "
        "al cliente informatico a traves de la API cuando se genere una "
        "decision automatizada."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D05[3])
    assert _nivel(resultado, "GR-D05-VERIF-CANAL") == NivelCobertura.AUSENTE


def prueba_comunicacion_a_usuario_final_es_explicita() -> None:
    texto = (
        "1.1. El sistema de IA debera informar al usuario mediante una "
        "notificacion cuando se genere una decision automatizada."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D05[3])
    assert _nivel(resultado, "GR-D05-VERIF-CANAL") == NivelCobertura.EXPLICITO


def prueba_explicabilidad_declarativa_es_parcial() -> None:
    resultado = _evaluar_texto(
        "2.1. El sistema debera proporcionar explicaciones adecuadas para "
        "las recomendaciones.",
        GUARDRAILS_D06[0],
    )
    assert _nivel(resultado, "GR-D06-PRES-EXPLICACION") == NivelCobertura.PARCIAL


def prueba_explicabilidad_con_factores_para_analista_es_explicita() -> None:
    texto = (
        "2.1. Ante una decision de rechazo, el sistema debera proporcionar "
        "una explicacion para el operador en formato de texto con los tres "
        "factores principales considerados y usar la explicacion de la "
        "decision para la revision."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D06)
    assert _nivel(resultado, "GR-D06-PRES-EXPLICACION") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D06-VERIF-FORMATO") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D06-CTRL-REVISION") == NivelCobertura.EXPLICITO


def prueba_explicacion_de_penalizacion_contractual_no_es_explicita() -> None:
    texto = (
        "8.1. El incumplimiento de los niveles especificados llevara "
        "asociado la aplicacion de penalizaciones, salvo justificacion "
        "pormenorizada del proveedor en la revision, y aceptacion de esta "
        "por parte del SMS."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D06[5])
    assert _nivel(resultado, "GR-D06-CTRL-REVISION") == NivelCobertura.PARCIAL


def prueba_supervision_humana_generica_es_parcial() -> None:
    resultado = _evaluar_texto(
        "3.1. Las decisiones podran ser revisadas por personal autorizado.",
        GUARDRAILS_D07[0],
    )
    assert _nivel(resultado, "GR-D07-PRES-HUMANO") == NivelCobertura.PARCIAL


def prueba_supervision_completa_es_explicita() -> None:
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


def prueba_ejemplo_oficial_d05_reconoce_voz_pasiva_y_limites() -> None:
    resultado = _evaluar_texto(
        "El usuario sera informado cuando una recomendacion sea generada "
        "por IA y recibira una descripcion de sus limites antes de "
        "confirmar la accion.",
        *GUARDRAILS_D05,
    )

    for codigo in (
        "GR-D05-PRES-IA",
        "GR-D05-DELIM-DESTINATARIOS",
        "GR-D05-DELIM-CONTENIDO",
        "GR-D05-VERIF-CANAL",
        "GR-D05-VERIF-LIMITES",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


def prueba_ejemplo_oficial_d06_reconoce_decision_y_analista() -> None:
    resultado = _evaluar_texto(
        "Ante una decision de rechazo, el sistema debera informar al "
        "analista los tres factores principales que influyeron en la "
        "salida y registrar la explicacion asociada.",
        *GUARDRAILS_D06,
    )

    for codigo in (
        "GR-D06-PRES-EXPLICACION",
        "GR-D06-DELIM-SALIDAS",
        "GR-D06-DELIM-DESTINATARIOS",
        "GR-D06-VERIF-FORMATO",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


def prueba_ejemplo_oficial_d07_reconoce_singular_y_alto_riesgo() -> None:
    resultado = _evaluar_texto(
        "Toda recomendacion de alto riesgo debera ser revisada por un "
        "supervisor autorizado, quien podra aprobarla, rechazarla o "
        "escalarla, registrando motivo y decision.",
        *GUARDRAILS_D07,
    )

    for codigo in (
        "GR-D07-PRES-HUMANO",
        "GR-D07-DELIM-DECISIONES",
        "GR-D07-DELIM-ROLES",
        "GR-D07-CTRL-INTERVENCION",
        "GR-D07-VERIF-ACTIVACION",
        "GR-D07-RESP-REGISTRO",
        "GR-D07-QUAL-DECLARATIVO",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


@pytest.mark.parametrize(
    "texto",
    (
        "El sistema debera registrar las decisiones en la base de datos.",
        "El sistema mostrara los factores configurados en formato JSON.",
        "El operador responsable revisara la calidad de los datos.",
        "Cuando el servidor falle, se ejecutara una revision tecnica.",
        "El sistema notificara al usuario por correo cuando cambie su contrasena.",
    ),
)
def prueba_contextos_tecnicos_no_generan_evidencia_etica(texto: str) -> None:
    resultado = _evaluar_texto(texto, *GUARDRAILS_D05_D07)

    assert all(
        aplicacion.hallazgo is not None
        and aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
        for aplicacion in resultado.aplicaciones
    )


def prueba_deteccion_no_depende_de_mayusculas_ni_acentos() -> None:
    resultado = _evaluar_texto(
        "TODA DECISIÓN DE ALTO RIESGO DEBERÁ SER REVISADA POR UN "
        "SUPERVISOR AUTORIZADO.",
        *GUARDRAILS_D07,
    )

    assert _nivel(
        resultado,
        "GR-D07-DELIM-DECISIONES",
    ) == NivelCobertura.EXPLICITO
    assert _nivel(
        resultado,
        "GR-D07-VERIF-ACTIVACION",
    ) == NivelCobertura.EXPLICITO


def prueba_integra_guardrails_d05_d07_con_calculo_de_cobertura() -> None:
    resultado = _evaluar_texto(
        "El usuario sera informado cuando una recomendacion sea generada "
        "por IA. La decision debera incluir una explicacion para el analista. "
        "Toda recomendacion de alto riesgo debera ser revisada por un "
        "supervisor autorizado.",
        *GUARDRAILS_D05_D07,
    )

    cobertura = calcular_cobertura_etica(resultado)

    assert tuple(
        dimension.dimension
        for dimension in cobertura.resultados_por_dimension
    ) == (DimensionEtica.D05, DimensionEtica.D06, DimensionEtica.D07)
    assert cobertura.indicadores_guardrails.guardrails_aplicados == 23


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


def prueba_reconoce_explicacion_por_factores_clave_y_sus_destinatarios() -> None:
    texto = (
        "El proveedor debera explicar al organismo y a los usuarios como se "
        "obtuvo cada resultado. La explicacion incluira una indicacion clara "
        "de los factores clave que llevaron a la decision."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D06)

    for codigo in (
        "GR-D06-PRES-EXPLICACION",
        "GR-D06-DELIM-SALIDAS",
        "GR-D06-DELIM-DESTINATARIOS",
        "GR-D06-VERIF-FORMATO",
        "GR-D06-RESP-EXPLICACION",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


def prueba_reconoce_autoridad_humana_para_revertir_e_interrumpir() -> None:
    texto = (
        "Las personas encargadas de la vigilancia humana podran desestimar, "
        "invalidar o revertir la informacion de salida. Tambien podran "
        "interrumpir el funcionamiento mediante un boton destinado a tal fin."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D07)

    for codigo in (
        "GR-D07-DELIM-ROLES",
        "GR-D07-CTRL-INTERVENCION",
        "GR-D07-VERIF-PROCEDIMIENTO",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO
