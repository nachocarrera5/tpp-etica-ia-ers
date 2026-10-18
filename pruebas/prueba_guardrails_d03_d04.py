"""Tests para los guardrails conceptuales de D03 (datos y privacidad) y
D04 (equidad y prevencion de sesgos).

Usa el pipeline NLP real (analizar_texto) y el MotorEvaluacionEtica para
validar comportamiento de extremo a extremo, siguiendo el mismo patron que
prueba_motor_evaluacion_etica.py.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    DimensionEtica,
    EstadoAplicacionGuardrail,
    NivelCobertura,
    PrioridadDocumental,
    SolicitudEvaluacionEtica,
    TipoVinculoEvidencia,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GR_D03_CTRL_RETENCION,
    GR_D03_DELIM_FINALIDAD,
    GR_D03_PRES_DATOS,
    GR_D03_QUAL_PRIVACIDAD,
    GR_D03_RESP_ACCESO,
    GR_D03_VERIF_CALIDAD,
    GR_D04_CTRL_MITIGACION,
    GR_D04_DELIM_GRUPOS,
    GR_D04_DELIM_PROXIES,
    GR_D04_PRES_SESGOS,
    GR_D04_QUAL_DECLARATIVO,
    GR_D04_RESP_REVISION,
    GR_D04_VERIF_METRICAS,
    GUARDRAILS_D03,
    GUARDRAILS_D03_D04,
    GUARDRAILS_D04,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto


def _evaluar_texto(texto: str, *guardrails):
    resultado_nlp = analizar_texto(texto)
    motor = MotorEvaluacionEtica(RepositorioGuardrailsEnMemoria(guardrails))
    resultado = motor.evaluar(
        SolicitudEvaluacionEtica(
            documento_id=uuid4(),
            resultado_nlp=resultado_nlp,
        )
    )
    return resultado


def _hallazgo_de(resultado, codigo: str):
    for aplicacion in resultado.aplicaciones:
        if aplicacion.guardrail_codigo == codigo:
            return aplicacion
    raise AssertionError(f"No se encontro aplicacion para {codigo}")


def prueba_catalogo_no_tiene_codigos_duplicados() -> None:
    codigos = [g.definicion.codigo for g in GUARDRAILS_D03_D04]
    assert len(codigos) == len(set(codigos))


def prueba_cita_de_titulo_normativo_rgpd_no_es_explicita() -> None:
    texto = (
        "Reglamento (UE) 2016/679 relativo a la proteccion de las personas "
        "fisicas en lo que respecta al tratamiento de datos personales y a "
        "la libre circulacion de estos datos."
    )
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)
    aplicacion = _hallazgo_de(resultado, "GR-D03-PRES-DATOS")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.PARCIAL


def prueba_cita_de_titulo_normativo_lopdgdd_no_es_explicita() -> None:
    texto = (
        "Ley Organica 3/2018, de 5 de diciembre, de Proteccion de Datos "
        "Personales y garantia de los derechos digitales."
    )
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)
    aplicacion = _hallazgo_de(resultado, "GR-D03-PRES-DATOS")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.PARCIAL


def prueba_categoria_real_de_datos_sigue_siendo_explicita() -> None:
    texto = (
        "El sistema debera procesar datos clinicos y datos financieros de "
        "los solicitantes para generar el puntaje de riesgo."
    )
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)
    aplicacion = _hallazgo_de(resultado, "GR-D03-PRES-DATOS")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_clausula_de_acceso_previo_generica_no_es_explicita() -> None:
    texto = (
        "El adjudicatario debera proporcionar al personal a su cargo, "
        "antes de acceder a informacion de FREMAP, procedimientos "
        "adecuados para realizar un uso adecuado de la misma."
    )
    resultado = _evaluar_texto(texto, GR_D03_RESP_ACCESO)
    aplicacion = _hallazgo_de(resultado, "GR-D03-RESP-ACCESO")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


def prueba_personal_autorizado_con_podra_acceder_sigue_siendo_explicita() -> None:
    texto = (
        "El personal autorizado podra acceder unicamente a los datos "
        "personales necesarios."
    )
    resultado = _evaluar_texto(texto, GR_D03_RESP_ACCESO)
    aplicacion = _hallazgo_de(resultado, "GR-D03-RESP-ACCESO")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_catalogo_se_puede_cargar_en_repositorio() -> None:
    repositorio = RepositorioGuardrailsEnMemoria(GUARDRAILS_D03_D04)
    assert len(repositorio.listar()) == 13


def prueba_guardrails_d03_estan_asociados_a_d03() -> None:
    for guardrail in GUARDRAILS_D03:
        assert DimensionEtica.D03 in guardrail.definicion.dimensiones


def prueba_guardrails_d04_estan_asociados_a_d04() -> None:
    for guardrail in GUARDRAILS_D04:
        assert DimensionEtica.D04 in guardrail.definicion.dimensiones


def prueba_todos_los_codigos_siguen_convencion_gr() -> None:
    for guardrail in GUARDRAILS_D03_D04:
        assert guardrail.definicion.codigo.startswith("GR-D0")


def prueba_ejemplo_datos_genericos_es_parcial() -> None:
    texto = (
        "2.1. El sistema debera usar informacion del usuario para "
        "generar una recomendacion personalizada."
    )
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)

    aplicacion = _hallazgo_de(resultado, "GR-D03-PRES-DATOS")
    assert aplicacion.estado == EstadoAplicacionGuardrail.APLICADO
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.PARCIAL
    assert aplicacion.hallazgo.evidencias[0].tipo_vinculo == (
        TipoVinculoEvidencia.CONTEXTUALIZA
    )
    evidencia = aplicacion.hallazgo.evidencias[0]
    assert evidencia.fragmentos_clave
    assert all(
        fragmento_clave in evidencia.texto
        for fragmento_clave in evidencia.fragmentos_clave
    )


def prueba_texto_sin_mencion_de_datos_es_ausente() -> None:
    texto = "2.1. El sistema debera responder en menos de dos segundos."
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)

    aplicacion = _hallazgo_de(resultado, "GR-D03-PRES-DATOS")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
    assert aplicacion.hallazgo.evidencias == ()


def prueba_ejemplo_equidad_declarativa_es_parcial() -> None:
    texto = "3.1. El sistema debera evitar sesgos y garantizar resultados justos."
    resultado = _evaluar_texto(texto, GR_D04_PRES_SESGOS)

    aplicacion = _hallazgo_de(resultado, "GR-D04-PRES-SESGOS")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.PARCIAL


def prueba_mencion_incidental_de_finalidad_no_es_evidencia_explicita() -> None:
    texto = "La documentacion estara disponible para la finalidad declarada."
    resultado = _evaluar_texto(texto, GR_D03_DELIM_FINALIDAD)

    aplicacion = _hallazgo_de(resultado, "GR-D03-DELIM-FINALIDAD")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


def prueba_prohibicion_de_uso_para_fin_distinto_es_explicita() -> None:
    texto = (
        "El adjudicatario no podra utilizar ni proporcionar a terceros "
        "datos o informacion de caracter personal para finalidades "
        "distintas a aquellas para las que los datos hubieran sido "
        "recogidos."
    )
    resultado = _evaluar_texto(texto, GR_D03_DELIM_FINALIDAD)

    aplicacion = _hallazgo_de(resultado, "GR-D03-DELIM-FINALIDAD")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_destruccion_o_borrado_irrecuperable_condicionado_es_explicita() -> None:
    texto = (
        "Una vez finalizado el contrato, el adjudicatario debera "
        "desarrollar las acciones necesarias para la transferencia de la "
        "informacion o la destruccion de la misma, incluyendo el borrado "
        "irrecuperable de cualquier informacion de FREMAP que ya no deba "
        "ser conservada."
    )
    resultado = _evaluar_texto(texto, GR_D03_CTRL_RETENCION)

    aplicacion = _hallazgo_de(resultado, "GR-D03-CTRL-RETENCION")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_destruccion_sin_condicion_de_retencion_no_es_explicita() -> None:
    texto = (
        "El edificio sufrio la destruccion parcial de su fachada durante "
        "el temporal de la semana pasada."
    )
    resultado = _evaluar_texto(texto, GR_D03_CTRL_RETENCION)

    aplicacion = _hallazgo_de(resultado, "GR-D03-CTRL-RETENCION")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


def prueba_requisitos_clinicos_identifican_datos_finalidad_acceso_y_borrado() -> None:
    texto = """
    El sistema generara la transcripcion del audio para su almacenamiento y
    procesamiento. Mantendra registros clinicos y grabaciones de audio.
    Implementara autenticacion de acceso para usuarios autorizados.
    Permitira eliminar de forma definitiva los registros clinicos cuando el
    paciente lo solicite.
    """
    resultado = _evaluar_texto(texto, *GUARDRAILS_D03)

    for codigo in (
        "GR-D03-PRES-DATOS",
        "GR-D03-DELIM-FINALIDAD",
        "GR-D03-RESP-ACCESO",
        "GR-D03-CTRL-RETENCION",
    ):
        aplicacion = _hallazgo_de(resultado, codigo)
        assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


@pytest.mark.parametrize(
    ("guardrail", "texto"),
    [
        (
            GR_D03_VERIF_CALIDAD,
            "El contrato tendra un periodo de 12 meses.",
        ),
        (
            GR_D03_RESP_ACCESO,
            "Los roles autorizados podran acceder al sistema.",
        ),
        (
            GR_D04_RESP_REVISION,
            "Se nombro un responsable designado para el despliegue.",
        ),
        (
            GR_D04_QUAL_DECLARATIVO,
            "Habra monitoreo continuo de la infraestructura.",
        ),
    ],
)
def prueba_no_confunde_contexto_tecnico_generico_con_evidencia_etica(
    guardrail,
    texto: str,
) -> None:
    resultado = _evaluar_texto(texto, guardrail)

    assert resultado.hallazgos[0].nivel_preliminar == NivelCobertura.AUSENTE


@pytest.mark.parametrize(
    ("guardrail", "texto"),
    [
        (
            GR_D03_DELIM_FINALIDAD,
            "Los datos personales se usaran exclusivamente para calcular "
            "el puntaje crediticio.",
        ),
        (
            GR_D03_VERIF_CALIDAD,
            "Los datos deberan estar completos al 95% y se actualizaran "
            "mensualmente.",
        ),
        (
            GR_D03_RESP_ACCESO,
            "El personal autorizado podra acceder unicamente a los datos "
            "personales necesarios.",
        ),
        (
            GR_D03_CTRL_RETENCION,
            "Se establece un periodo de retencion de 12 meses.",
        ),
        (
            GR_D03_QUAL_PRIVACIDAD,
            "Se solicitara el consentimiento informado de los usuarios.",
        ),
        (
            GR_D04_DELIM_GRUPOS,
            "La precision se medira para mujeres, personas mayores y "
            "poblacion rural.",
        ),
        (
            GR_D04_DELIM_PROXIES,
            "Los atributos sensibles como genero y discapacidad seran "
            "revisados antes del entrenamiento.",
        ),
        (
            GR_D04_VERIF_METRICAS,
            "La tasa de falsos positivos no debera diferir mas de 5 puntos "
            "entre mujeres y hombres.",
        ),
        (
            GR_D04_CTRL_MITIGACION,
            "Si la brecha supera el 5%, el comite suspendera el despliegue "
            "y ajustara el modelo.",
        ),
        (
            GR_D04_RESP_REVISION,
            "El comite evaluara las diferencias de desempeno por grupo.",
        ),
        (
            GR_D04_QUAL_DECLARATIVO,
            "Habra monitoreo continuo ante cambios en los datos.",
        ),
    ],
)
def prueba_reconoce_evidencia_explicita_con_formulaciones_equivalentes(
    guardrail,
    texto: str,
) -> None:
    resultado = _evaluar_texto(texto, guardrail)

    assert resultado.hallazgos[0].nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_ausencia_total_de_mencion_a_sesgos_es_ausente() -> None:
    texto = "3.1. El sistema debera clasificar solicitudes de credito."
    resultado = _evaluar_texto(texto, GR_D04_PRES_SESGOS)

    aplicacion = _hallazgo_de(resultado, "GR-D04-PRES-SESGOS")
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


def prueba_ejemplo_evidencia_explicita_d03() -> None:
    texto = (
        "4.1. Los datos de entrenamiento deberan proceder de registros "
        "autorizados de los ultimos 24 meses, excluir variables no "
        "necesarias para la finalidad declarada y documentar limitaciones "
        "conocidas del dataset."
    )
    resultado = _evaluar_texto(
        texto,
        GR_D03_PRES_DATOS,
        GR_D03_DELIM_FINALIDAD,
        GR_D03_VERIF_CALIDAD,
    )

    assert _hallazgo_de(resultado, "GR-D03-PRES-DATOS").hallazgo.nivel_preliminar == (
        NivelCobertura.EXPLICITO
    )
    assert _hallazgo_de(
        resultado, "GR-D03-DELIM-FINALIDAD"
    ).hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado, "GR-D03-VERIF-CALIDAD"
    ).hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert all(
        evidencia.tipo_vinculo == TipoVinculoEvidencia.SOPORTA
        for hallazgo in resultado.hallazgos
        for evidencia in hallazgo.evidencias
    )


def prueba_ejemplo_evidencia_explicita_d04() -> None:
    texto = (
        "4.2. El sistema debera reportar desempeno por grupo etario y "
        "genero, y activar revision del responsable designado si la "
        "diferencia de falsos negativos entre subgrupos supera el "
        "umbral definido para el dominio."
    )
    resultado = _evaluar_texto(
        texto,
        GR_D04_PRES_SESGOS,
        GR_D04_DELIM_GRUPOS,
        GR_D04_CTRL_MITIGACION,
        GR_D04_RESP_REVISION,
    )

    assert _hallazgo_de(
        resultado, "GR-D04-PRES-SESGOS"
    ).hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado, "GR-D04-DELIM-GRUPOS"
    ).hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado, "GR-D04-CTRL-MITIGACION"
    ).hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado, "GR-D04-RESP-REVISION"
    ).hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_nivel_ausente_tiene_prioridad_alta_y_revision() -> None:
    texto = "5.1. El sistema debera procesar solicitudes en tiempo real."
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)

    hallazgo = _hallazgo_de(resultado, "GR-D03-PRES-DATOS").hallazgo
    assert hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
    assert hallazgo.prioridad_documental == PrioridadDocumental.ALTA
    assert hallazgo.requiere_revision_humana is True


def prueba_nivel_explicito_igual_requiere_revision_humana() -> None:
    texto = (
        "5.2. Los datos de entrenamiento deberan proceder de registros "
        "autorizados de los ultimos 24 meses."
    )
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)

    hallazgo = _hallazgo_de(resultado, "GR-D03-PRES-DATOS").hallazgo
    assert hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert hallazgo.requiere_revision_humana is True
    assert "no certifica" in hallazgo.motivo_revision_humana.lower()


@pytest.mark.parametrize(
    ("texto", "nivel"),
    [
        (
            "El sistema debera responder en menos de dos segundos.",
            NivelCobertura.AUSENTE,
        ),
        (
            "Los datos personales procederan de registros autorizados.",
            NivelCobertura.EXPLICITO,
        ),
    ],
)
def prueba_prioridad_es_independiente_del_nivel(
    texto: str,
    nivel: NivelCobertura,
) -> None:
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)

    hallazgo = resultado.hallazgos[0]
    assert hallazgo.nivel_preliminar == nivel
    assert hallazgo.prioridad_documental == PrioridadDocumental.ALTA
    assert "independiente del nivel" in hallazgo.justificacion_prioridad


def prueba_documento_solo_encabezados_no_aplica() -> None:
    texto = "3. Requisitos Especificos"
    resultado = _evaluar_texto(texto, GR_D03_PRES_DATOS)

    aplicacion = _hallazgo_de(resultado, "GR-D03-PRES-DATOS")
    assert aplicacion.estado == EstadoAplicacionGuardrail.NO_APLICABLE
    assert aplicacion.hallazgo is None


def prueba_evidencia_referencia_fragmento_real_del_documento() -> None:
    texto = "2.1. El sistema debera usar datos del usuario para su operacion."
    resultado_nlp = analizar_texto(texto)
    fragmento = resultado_nlp.fragmentos_clasificados[0].fragmento

    motor = MotorEvaluacionEtica(
        RepositorioGuardrailsEnMemoria((GR_D03_PRES_DATOS,))
    )
    resultado = motor.evaluar(
        SolicitudEvaluacionEtica(documento_id=uuid4(), resultado_nlp=resultado_nlp)
    )

    hallazgo = _hallazgo_de(resultado, "GR-D03-PRES-DATOS").hallazgo
    assert hallazgo.evidencias[0].fragmento_id == fragmento.id
    assert hallazgo.evidencias[0].texto == fragmento.texto


def prueba_catalogo_completo_sobre_documento_con_evidencia_mixta() -> None:
    texto = (
        "3. Requisitos Especificos\n\n"
        "3.1. El sistema debera usar informacion del usuario para generar "
        "una recomendacion personalizada.\n\n"
        "3.2. El sistema debera evitar sesgos y garantizar resultados "
        "justos."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D03_D04)

    assert len(resultado.aplicaciones) == 13
    estados = {a.guardrail_codigo: a.estado for a in resultado.aplicaciones}
    assert all(
        estado == EstadoAplicacionGuardrail.APLICADO
        for estado in estados.values()
    )

    assert _hallazgo_de(
        resultado, "GR-D03-PRES-DATOS"
    ).hallazgo.nivel_preliminar == NivelCobertura.PARCIAL

    assert _hallazgo_de(
        resultado, "GR-D04-PRES-SESGOS"
    ).hallazgo.nivel_preliminar == NivelCobertura.PARCIAL

    assert _hallazgo_de(
        resultado, "GR-D03-CTRL-RETENCION"
    ).hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
    assert _hallazgo_de(
        resultado, "GR-D04-DELIM-PROXIES"
    ).hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


@pytest.mark.parametrize(
    "guardrail",
    GUARDRAILS_D03_D04,
    ids=[g.definicion.codigo for g in GUARDRAILS_D03_D04],
)
def prueba_cada_guardrail_produce_ausente_sobre_texto_neutro(guardrail) -> None:
    texto = "9.1. El sistema debera mostrar un mensaje de bienvenida al usuario."
    resultado = _evaluar_texto(texto, guardrail)

    aplicacion = resultado.aplicaciones[0]
    assert aplicacion.estado == EstadoAplicacionGuardrail.APLICADO
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


def prueba_reconoce_prevencion_y_mitigacion_explicita_de_sesgos() -> None:
    texto = (
        "El proveedor implementara mecanismos para asegurar que las decisiones "
        "tomadas por la IA no perpetuen ni generen nuevos sesgos."
    )
    resultado = _evaluar_texto(
        texto,
        GR_D04_PRES_SESGOS,
        GR_D04_CTRL_MITIGACION,
    )

    assert all(
        aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
        for aplicacion in resultado.aplicaciones
    )


def prueba_reconoce_responsable_de_acceso_a_modelos_y_datos() -> None:
    texto = (
        "El ingeniero de seguridad con foco en IA debera establecer controles "
        "de acceso a modelos y datos e implementar cifrado de datos sensibles."
    )
    resultado = _evaluar_texto(texto, GR_D03_RESP_ACCESO)

    assert _hallazgo_de(
        resultado, "GR-D03-RESP-ACCESO"
    ).hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_reconoce_control_y_responsable_de_revision_de_sesgos() -> None:
    texto = (
        "El marco incluira sistemas fundamentales de control de sesgos. "
        "El especialista en etica y cumplimiento de IA creara protocolos de "
        "evaluacion de sesgos y fairness y coordinara auditorias eticas."
    )
    resultado = _evaluar_texto(
        texto,
        GR_D04_PRES_SESGOS,
        GR_D04_RESP_REVISION,
    )

    assert all(
        aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
        for aplicacion in resultado.aplicaciones
    )


def prueba_destruccion_condicionada_de_bienes_no_es_retencion_de_datos() -> None:
    texto = "Al finalizar la obra se procedera a la destruccion del edificio."
    resultado = _evaluar_texto(texto, GR_D03_CTRL_RETENCION)
    aplicacion = _hallazgo_de(resultado, "GR-D03-CTRL-RETENCION")
    assert aplicacion.hallazgo.nivel_preliminar != NivelCobertura.EXPLICITO
