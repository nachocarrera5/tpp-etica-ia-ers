from __future__ import annotations

from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    DimensionEtica,
    EstadoAplicacionGuardrail,
    FamiliaGuardrail,
    NivelCobertura,
    SolicitudEvaluacionEtica,
    TipoVinculoEvidencia,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GR_D01_DELIM_ACTORES,
    GR_D01_DELIM_ALCANCE,
    GR_D01_DELIM_USOS,
    GR_D01_PRES_PROPOSITO,
    GR_D01_QUAL_PROPOSITO,
    GR_D01_VERIF_LIMITACIONES,
    GR_D01_VERIF_SUPUESTOS,
    GR_D02_CTRL_REVISION,
    GR_D02_DELIM_INDIRECTOS,
    GR_D02_DELIM_VULNERABLES,
    GR_D02_PRES_ACTORES,
    GR_D02_QUAL_IMPACTO,
    GR_D02_RESP_ACTORES,
    GR_D02_VERIF_BENEFICIOS,
    GR_D02_VERIF_IMPACTOS,
    GUARDRAILS_D01,
    GUARDRAILS_D01_D02,
    GUARDRAILS_D02,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto


CODIGOS_D01 = (
    "GR-D01-PRES-PROPOSITO",
    "GR-D01-DELIM-ALCANCE",
    "GR-D01-DELIM-USOS",
    "GR-D01-DELIM-ACTORES",
    "GR-D01-VERIF-SUPUESTOS",
    "GR-D01-VERIF-LIMITACIONES",
    "GR-D01-QUAL-PROPOSITO",
)

CODIGOS_D02 = (
    "GR-D02-PRES-ACTORES",
    "GR-D02-DELIM-INDIRECTOS",
    "GR-D02-DELIM-VULNERABLES",
    "GR-D02-VERIF-IMPACTOS",
    "GR-D02-VERIF-BENEFICIOS",
    "GR-D02-CTRL-REVISION",
    "GR-D02-RESP-ACTORES",
    "GR-D02-QUAL-IMPACTO",
)

CRITERIOS_ESPERADOS = {
    "GR-D01-PRES-PROPOSITO": ("D01-C1",),
    "GR-D01-DELIM-ALCANCE": ("D01-C2",),
    "GR-D01-DELIM-USOS": ("D01-C4", "D01-C5"),
    "GR-D01-DELIM-ACTORES": ("D01-C3",),
    "GR-D01-VERIF-SUPUESTOS": ("D01-C6",),
    "GR-D01-VERIF-LIMITACIONES": ("D01-C7",),
    "GR-D01-QUAL-PROPOSITO": ("D01-C1", "D01-C8"),
    "GR-D02-PRES-ACTORES": ("D02-C1", "D02-C2", "D02-C3"),
    "GR-D02-DELIM-INDIRECTOS": ("D02-C3",),
    "GR-D02-DELIM-VULNERABLES": ("D02-C4",),
    "GR-D02-VERIF-IMPACTOS": ("D02-C6",),
    "GR-D02-VERIF-BENEFICIOS": ("D02-C5",),
    "GR-D02-CTRL-REVISION": ("D02-C7",),
    "GR-D02-RESP-ACTORES": ("D02-C2", "D02-C7"),
    "GR-D02-QUAL-IMPACTO": ("D02-C5", "D02-C6", "D02-C8"),
}

FAMILIAS_ESPERADAS = {
    "GR-D01-PRES-PROPOSITO": FamiliaGuardrail.PRESENCIA,
    "GR-D01-DELIM-ALCANCE": FamiliaGuardrail.DELIMITACION,
    "GR-D01-DELIM-USOS": FamiliaGuardrail.DELIMITACION,
    "GR-D01-DELIM-ACTORES": FamiliaGuardrail.DELIMITACION,
    "GR-D01-VERIF-SUPUESTOS": FamiliaGuardrail.VERIFICABILIDAD,
    "GR-D01-VERIF-LIMITACIONES": FamiliaGuardrail.VERIFICABILIDAD,
    "GR-D01-QUAL-PROPOSITO": FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    "GR-D02-PRES-ACTORES": FamiliaGuardrail.PRESENCIA,
    "GR-D02-DELIM-INDIRECTOS": FamiliaGuardrail.DELIMITACION,
    "GR-D02-DELIM-VULNERABLES": FamiliaGuardrail.DELIMITACION,
    "GR-D02-VERIF-IMPACTOS": FamiliaGuardrail.VERIFICABILIDAD,
    "GR-D02-VERIF-BENEFICIOS": FamiliaGuardrail.VERIFICABILIDAD,
    "GR-D02-CTRL-REVISION": FamiliaGuardrail.CONTROL,
    "GR-D02-RESP-ACTORES": FamiliaGuardrail.RESPONSABILIDAD,
    "GR-D02-QUAL-IMPACTO": FamiliaGuardrail.CALIDAD_DOCUMENTAL,
}


def _evaluar_texto(texto: str, *guardrails):
    resultado_nlp = analizar_texto(texto)
    motor = MotorEvaluacionEtica(RepositorioGuardrailsEnMemoria(guardrails))
    return motor.evaluar(
        SolicitudEvaluacionEtica(
            documento_id=uuid4(),
            resultado_nlp=resultado_nlp,
        )
    )


def _hallazgo_de(resultado, codigo: str):
    for aplicacion in resultado.aplicaciones:
        if aplicacion.guardrail_codigo == codigo:
            return aplicacion.hallazgo
    raise AssertionError(f"No se encontro aplicacion para {codigo}")


def prueba_catalogo_coincide_con_la_matriz_d01_d02() -> None:
    assert tuple(g.definicion.codigo for g in GUARDRAILS_D01) == CODIGOS_D01
    assert tuple(g.definicion.codigo for g in GUARDRAILS_D02) == CODIGOS_D02
    assert len(GUARDRAILS_D01_D02) == 15


def prueba_trabajadores_de_prevencion_de_riesgos_laborales_no_es_evidencia() -> None:
    texto = (
        "Antes del comienzo de la actividad, la empresa adjudicataria "
        "facilitara a sus trabajadores la totalidad de EPIs derivada de "
        "su evaluacion de riesgos."
    )
    resultado = _evaluar_texto(texto, GR_D02_PRES_ACTORES)
    hallazgo = _hallazgo_de(resultado, "GR-D02-PRES-ACTORES")
    assert hallazgo.nivel_preliminar == NivelCobertura.AUSENTE


def prueba_trabajadores_como_afectados_reales_sigue_siendo_evidencia() -> None:
    texto = (
        "El sistema de IA evaluara el desempeno de los trabajadores de la "
        "empresa para recomendar ascensos."
    )
    resultado = _evaluar_texto(texto, GR_D02_PRES_ACTORES)
    hallazgo = _hallazgo_de(resultado, "GR-D02-PRES-ACTORES")
    assert hallazgo.nivel_preliminar == NivelCobertura.PARCIAL


def prueba_catalogo_no_tiene_identidades_duplicadas() -> None:
    repositorio = RepositorioGuardrailsEnMemoria(GUARDRAILS_D01_D02)

    assert repositorio.listar() == GUARDRAILS_D01_D02


def prueba_definiciones_preservan_dimensiones_familias_y_criterios() -> None:
    for guardrail in GUARDRAILS_D01_D02:
        definicion = guardrail.definicion
        dimension = (
            DimensionEtica.D01
            if definicion.codigo.startswith("GR-D01")
            else DimensionEtica.D02
        )

        assert definicion.dimensiones == (dimension,)
        assert definicion.familia == FAMILIAS_ESPERADAS[definicion.codigo]
        assert definicion.criterios == CRITERIOS_ESPERADOS[definicion.codigo]


@pytest.mark.parametrize(
    ("guardrail", "texto"),
    [
        (
            GR_D01_PRES_PROPOSITO,
            "El objetivo del sistema es asistir a profesionales de salud.",
        ),
        (
            GR_D01_DELIM_ALCANCE,
            "El dominio de aplicacion sera credito minorista.",
        ),
        (
            GR_D01_DELIM_USOS,
            "El sistema no se usara para decisiones disciplinarias.",
        ),
        (
            GR_D01_DELIM_ACTORES,
            "El sistema sera utilizado por analistas de credito.",
        ),
        (
            GR_D01_VERIF_SUPUESTOS,
            "Se asume que las solicitudes contienen datos completos.",
        ),
        (
            GR_D01_VERIF_LIMITACIONES,
            "El sistema no reemplaza la decision del profesional.",
        ),
        (
            GR_D01_QUAL_PROPOSITO,
            "El objetivo medible es reducir los rechazos erroneos un 20%.",
        ),
        (
            GR_D02_PRES_ACTORES,
            "Los usuarios directos seran analistas y supervisores.",
        ),
        (
            GR_D02_DELIM_INDIRECTOS,
            "Los afectados indirectos seran los garantes.",
        ),
        (
            GR_D02_DELIM_VULNERABLES,
            "Los grupos vulnerables incluyen personas con baja conectividad.",
        ),
        (
            GR_D02_VERIF_IMPACTOS,
            "El riesgo de exclusion afecta a solicitantes sin historial.",
        ),
        (
            GR_D02_VERIF_BENEFICIOS,
            "La mejora esperada sera para los usuarios finales.",
        ),
        (
            GR_D02_CTRL_REVISION,
            "Si se detectan impactos no previstos, el equipo investigara "
            "y corregira la causa.",
        ),
        (
            GR_D02_RESP_ACTORES,
            "El comite responsable revisara los impactos sobre afectados.",
        ),
        (
            GR_D02_QUAL_IMPACTO,
            "El riesgo de exclusion sobre solicitantes sera revisado cuando "
            "cambie el dominio.",
        ),
    ],
    ids=[guardrail.definicion.codigo for guardrail in GUARDRAILS_D01_D02],
)
def prueba_cada_guardrail_reconoce_evidencia_explicita(
    guardrail,
    texto: str,
) -> None:
    resultado = _evaluar_texto(texto, guardrail)

    hallazgo = resultado.hallazgos[0]
    assert hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert hallazgo.evidencias[0].tipo_vinculo == TipoVinculoEvidencia.SOPORTA


def prueba_evidencia_generica_es_parcial_y_contextual() -> None:
    resultado = _evaluar_texto(
        "La ERS contiene una evaluacion de impacto.",
        GR_D02_QUAL_IMPACTO,
    )

    hallazgo = resultado.hallazgos[0]
    assert hallazgo.nivel_preliminar == NivelCobertura.PARCIAL
    assert hallazgo.evidencias[0].tipo_vinculo == (
        TipoVinculoEvidencia.CONTEXTUALIZA
    )


def prueba_ejemplo_oficial_d01_no_queda_ausente() -> None:
    texto = (
        "El sistema priorizara solicitudes internas de soporte tecnico. "
        "No se usara para decisiones disciplinarias ni evaluacion de "
        "desempeno."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D01)

    assert _hallazgo_de(
        resultado,
        "GR-D01-PRES-PROPOSITO",
    ).nivel_preliminar == NivelCobertura.PARCIAL
    assert _hallazgo_de(
        resultado,
        "GR-D01-DELIM-ALCANCE",
    ).nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado,
        "GR-D01-DELIM-USOS",
    ).nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_ejemplo_oficial_d02_reconoce_actores_e_impacto() -> None:
    texto = (
        "La ERS identifica como afectados directos a solicitantes de credito "
        "y como afectados indirectos a garantes. Se reconoce el riesgo de "
        "exclusion en grupos con historial crediticio limitado."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D02)

    assert _hallazgo_de(
        resultado,
        "GR-D02-PRES-ACTORES",
    ).nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado,
        "GR-D02-DELIM-INDIRECTOS",
    ).nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado,
        "GR-D02-DELIM-VULNERABLES",
    ).nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado,
        "GR-D02-VERIF-IMPACTOS",
    ).nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado,
        "GR-D02-QUAL-IMPACTO",
    ).nivel_preliminar == NivelCobertura.EXPLICITO


@pytest.mark.parametrize(
    ("guardrail", "texto"),
    [
        (
            GR_D01_PRES_PROPOSITO,
            "El proposito del documento es describir la instalacion.",
        ),
        (
            GR_D02_RESP_ACTORES,
            "Existe un responsable tecnico del despliegue.",
        ),
        (
            GR_D02_CTRL_REVISION,
            "El monitoreo continuo registrara el uso de CPU.",
        ),
        (
            GR_D02_VERIF_IMPACTOS,
            "La actualizacion tiene impacto en el rendimiento tecnico.",
        ),
    ],
)
def prueba_no_confunde_contexto_tecnico_con_evidencia_etica(
    guardrail,
    texto: str,
) -> None:
    resultado = _evaluar_texto(texto, guardrail)

    assert resultado.hallazgos[0].nivel_preliminar == NivelCobertura.AUSENTE


@pytest.mark.parametrize(
    "guardrail",
    GUARDRAILS_D01_D02,
    ids=[guardrail.definicion.codigo for guardrail in GUARDRAILS_D01_D02],
)
def prueba_texto_neutro_no_genera_evidencia(guardrail) -> None:
    resultado = _evaluar_texto(
        "El sistema almacenara un valor interno.",
        guardrail,
    )

    aplicacion = resultado.aplicaciones[0]
    assert aplicacion.estado == EstadoAplicacionGuardrail.APLICADO
    assert aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
    assert aplicacion.hallazgo.evidencias == ()


def prueba_documento_solo_con_encabezado_no_aplica() -> None:
    resultado = _evaluar_texto(
        "2. Stakeholders e impacto",
        GR_D02_PRES_ACTORES,
    )

    assert resultado.aplicaciones[0].estado == (
        EstadoAplicacionGuardrail.NO_APLICABLE
    )
    assert resultado.aplicaciones[0].hallazgo is None


def prueba_reconoce_proposito_y_alcance_formulados_como_contrato() -> None:
    texto = (
        "El objeto del contrato es desarrollar una solucion de IA que permita "
        "agilizar la evaluacion de solicitudes. El alcance del contrato "
        "comprende el sistema aplicado a expedientes de empleo."
    )
    resultado = _evaluar_texto(
        texto,
        GR_D01_PRES_PROPOSITO,
        GR_D01_DELIM_ALCANCE,
    )

    assert _hallazgo_de(
        resultado, "GR-D01-PRES-PROPOSITO"
    ).nivel_preliminar == NivelCobertura.EXPLICITO
    assert _hallazgo_de(
        resultado, "GR-D01-DELIM-ALCANCE"
    ).nivel_preliminar == NivelCobertura.EXPLICITO


def prueba_reconoce_grupo_vulnerable_y_beneficio_publico() -> None:
    texto = (
        "La solucion tramita subvenciones de empleo para personas con "
        "discapacidad y busca mejorar el servicio ofrecido a la ciudadania."
    )
    resultado = _evaluar_texto(
        texto,
        GR_D02_DELIM_VULNERABLES,
        GR_D02_VERIF_BENEFICIOS,
    )

    assert all(
        aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
        for aplicacion in resultado.aplicaciones
    )


def prueba_reconoce_proposito_alcance_y_usuarios_de_un_marco_de_ia() -> None:
    texto = (
        "El presente contrato tiene por objeto el desarrollo de un marco de "
        "trabajo corporativo para inteligencia artificial. Este marco permitira "
        "abordar la generacion de aplicaciones de IA generativa. El marco "
        "dara cabida a componentes relacionados con IA generativa, "
        "incluidos modelos de IA, sistemas RAG y agentes de IA. "
        "La aplicacion permite disponer de dos tipos de usuarios: administrador "
        "y usuario."
    )
    resultado = _evaluar_texto(
        texto,
        GR_D01_PRES_PROPOSITO,
        GR_D01_DELIM_ALCANCE,
        GR_D01_DELIM_ACTORES,
    )

    assert all(
        aplicacion.hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
        for aplicacion in resultado.aplicaciones
    )


def prueba_condiciones_contractuales_no_son_supuestos_del_sistema() -> None:
    texto = (
        "La solucion debera estar basada, siempre que sea posible, en "
        "tecnologia de contenedores."
    )
    resultado = _evaluar_texto(texto, GR_D01_VERIF_SUPUESTOS)

    assert _hallazgo_de(
        resultado, "GR-D01-VERIF-SUPUESTOS"
    ).nivel_preliminar == NivelCobertura.AUSENTE


def prueba_limite_del_equipo_contractual_no_es_limitacion_del_sistema() -> None:
    texto = "El equipo de trabajo en ningun caso podra ser mayor de siete personas."
    resultado = _evaluar_texto(texto, GR_D01_VERIF_LIMITACIONES)

    assert _hallazgo_de(
        resultado, "GR-D01-VERIF-LIMITACIONES"
    ).nivel_preliminar == NivelCobertura.AUSENTE


def prueba_recomendacion_que_no_sustituye_decision_es_limitacion() -> None:
    texto = (
        "La recomendacion sera orientativa y no sustituira la evaluacion "
        "profesional de las circunstancias particulares."
    )
    resultado = _evaluar_texto(texto, GR_D01_VERIF_LIMITACIONES)

    assert _hallazgo_de(
        resultado, "GR-D01-VERIF-LIMITACIONES"
    ).nivel_preliminar == NivelCobertura.EXPLICITO
