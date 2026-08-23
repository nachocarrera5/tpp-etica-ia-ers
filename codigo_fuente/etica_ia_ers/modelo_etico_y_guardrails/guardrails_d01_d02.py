from __future__ import annotations

from typing import Tuple

from etica_ia_ers.dominio import (
    DefinicionGuardrail,
    DimensionEtica,
    EstadoGuardrail,
    FamiliaGuardrail,
    PrioridadDocumental,
)

from .guardrail_lexico import GuardrailLexico, senal


GR_D01_PRES_PROPOSITO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-PRES-PROPOSITO",
        nombre="Presencia y definicion del proposito del sistema",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si la ERS describe claramente el proposito o "
            "finalidad general del sistema (p.ej. objetivos y alcance)."
        ),
        criterios=("D01-C1",),
        prioridad_base=PrioridadDocumental.MEDIA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal("proposito_declarado", r"prop[oó]sito\s+del\s+sistema"),
        senal("finalidad_declarada", r"finalidad\s+(?:del|de\s+uso)\s+del\s+sistema"),
    ),
    senales_parciales=(
        senal("mencion_proposito_generica", r"proposito|finalidad"),
        senal("mencion_objetivos", r"objetivos\s+(?:del\s+)?sistema"),
    ),
)


GR_D02_CONTEXTO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-CONTEXTO",
        nombre="Contexto y entorno de despliegue",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se describe el contexto de uso, entornos de "
            "despliegue y limitaciones operativas del sistema."
        ),
        criterios=("D02-C1",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("contexto_de_uso", r"contexto\s+de\s+uso|entorno\s+de\s+despliegue"),
        senal("ambito_aplicacion", r"\bambito\s+de\s+aplicaci[oó]n\b"),
    ),
    senales_parciales=(
        senal("mencion_contexto_generico", r"contexto|entorno|ambito"),
    ),
)


GR_D02_STAKEHOLDERS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-STAKEHOLDERS",
        nombre="Identificacion de stakeholders y responsables",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.RESPONSABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si la ERS identifica stakeholders, partes "
            "interesadas y responsables relacionados con el sistema."
        ),
        criterios=("D02-C2",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal("stakeholders_identificados", r"stakeholders|partes?\s+interesadas"),
        senal("responsables_definidos", r"responsables?\s+(?:designad[oa]s?|identificad[oa]s|del\s+sistema)"),
    ),
    senales_parciales=(
        senal("mencion_responsable_generico", r"responsable|equipo\s+responsable"),
    ),
)


GR_D02_IMPACTO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-IMPACTO",
        nombre="Evaluacion de impacto y riesgos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se realiza una evaluacion de impacto, se "
            "identifican riesgos y consecuencias para usuarios o grupos."
        ),
        criterios=("D02-C3",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal("evaluacion_impacto", r"evaluaci[oó]n\s+de\s+impacto"),
        senal("riesgos_identificados", r"riesgos?\s+identificados|impacto[s]?\s+en\s+usuarios"),
    ),
    senales_parciales=(
        senal("mencion_riesgo_generico", r"riesgo|impacto|consecuencia[s]?")
    ),
)


GUARDRAILS_D01: Tuple[GuardrailLexico, ...] = (
    GR_D01_PRES_PROPOSITO,
)


GR_D01_DELIM_ALCANCE = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-DELIM-ALCANCE",
        nombre="Delimitacion del alcance",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se delimita el alcance operacional y limites del proposito."
        ),
        criterios=("D01-C2",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("alcance_definido", r"alcance\s+del\s+sistema|alcance\s+operacional"),
    ),
    senales_parciales=(
        senal("mencion_alcance_generico", r"alcance"),
    ),
)

GR_D01_DELIM_USOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-DELIM-USOS",
        nombre="Delimitacion de usos aceptables",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se especifican usos aceptables o restricciones de uso."
        ),
        criterios=("D01-C3",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("usos_aceptables", r"usos?\s+aceptables|prohibid[oa]s|no\s+permitido"),
    ),
    senales_parciales=(
        senal("mencion_usos_generico", r"uso[s]?|aplicaci[oó]n"),
    ),
)

GR_D01_DELIM_ACTORES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-DELIM-ACTORES",
        nombre="Delimitacion de actores y roles",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se describen actores, roles y responsabilidades en el proposito."
        ),
        criterios=("D01-C4",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("actores_definidos", r"actores\s+involucrad[oa]s|roles\s+definidos"),
    ),
    senales_parciales=(
        senal("mencion_actores_generico", r"actores|roles|partes?\s+interesadas"),
    ),
)

GR_D01_VERIF_SUPUESTOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-VERIF-SUPUESTOS",
        nombre="Verificabilidad de supuestos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si los supuestos operativos del proposito estan documentados y verificables."
        ),
        criterios=("D01-C5",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("supuestos_documentados", r"supuestos\s+operativ[oa]s|supuestos\s+del\s+sistema"),
    ),
    senales_parciales=(
        senal("mencion_supuestos_generico", r"supuestos"),
    ),
)

GR_D01_VERIF_LIMITACIONES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-VERIF-LIMITACIONES",
        nombre="Verificabilidad de limitaciones",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se documentan limitaciones conocidas del proposito y su impacto."
        ),
        criterios=("D01-C6",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("limitaciones_documentadas", r"limitaciones\s+conocidas|limites\s+operativos"),
    ),
    senales_parciales=(
        senal("mencion_limitaciones_generico", r"limitacion|limitaciones|limite"),
    ),
)

GR_D01_QUAL_PROPOSITO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-QUAL-PROPOSITO",
        nombre="Calidad documental del proposito",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CALIDAD_DOCUMENTAL,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si las declaraciones sobre el proposito son verificables y no puramente declarativas."
        ),
        criterios=("D01-C7",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("proposito_verificable", r"proposito\s+verificable|objetivos\s+medibles"),
    ),
    senales_parciales=(
        senal("mencion_calidad_proposito", r"verificable|medible|traceable|rastreable"),
    ),
)

GUARDRAILS_D01 = (
    GR_D01_PRES_PROPOSITO,
    GR_D01_DELIM_ALCANCE,
    GR_D01_DELIM_USOS,
    GR_D01_DELIM_ACTORES,
    GR_D01_VERIF_SUPUESTOS,
    GR_D01_VERIF_LIMITACIONES,
    GR_D01_QUAL_PROPOSITO,
)


GR_D02_PRES_ACTORES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-PRES-ACTORES",
        nombre="Presencia de actores relacionados",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.PRESENCIA,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se listan actores directos e indirectos afectados por el sistema."
        ),
        criterios=("D02-C1",),
        prioridad_base=PrioridadDocumental.ALTA,
    ),
    senales_explicitas=(
        senal("actores_listados", r"actores\s+afectad[oa]s|grupos\s+afectad[oa]s"),
    ),
    senales_parciales=(
        senal("mencion_actores_generico", r"actores|grupos|usuarios"),
    ),
)

GR_D02_DELIM_INDIRECTOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-DELIM-INDIRECTOS",
        nombre="Delimitacion de afectados indirectos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se consideran impactos en afectados indirectos o por externalidades."
        ),
        criterios=("D02-C2",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("afectados_indirectos", r"afectados\s+indirectos|externalidades"),
    ),
    senales_parciales=(
        senal("mencion_indirectos_generico", r"indirectos|externalidad"),
    ),
)

GR_D02_DELIM_VULNERABLES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-DELIM-VULNERABLES",
        nombre="Delimitacion de grupos vulnerables",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se identifican grupos vulnerables y consideraciones especiales."
        ),
        criterios=("D02-C3",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal("grupos_vulnerables", r"vulnerables|grupos\s+vulnerables"),
    ),
    senales_parciales=(
        senal("mencion_vulnerables_generico", r"vulnerabl[e|es]?"),
    ),
)

GR_D02_VERIF_IMPACTOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-VERIF-IMPACTOS",
        nombre="Verificabilidad de impactos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si los impactos previstos estan documentados con criterios verificables."
        ),
        criterios=("D02-C4",),
        prioridad_base=PrioridadDocumental.ALTA,
    ),
    senales_explicitas=(
        senal("impactos_documentados", r"impactos?\s+documentad[oa]s|impacto[s]?\s+previstos"),
    ),
    senales_parciales=(
        senal("mencion_impacto_generico", r"impacto|consecuencia"),
    ),
)

GR_D02_VERIF_BENEFICIOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-VERIF-BENEFICIOS",
        nombre="Verificabilidad de beneficios",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si los beneficios esperados del sistema estan descritos y medibles."
        ),
        criterios=("D02-C5",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("beneficios_descriptos", r"beneficios?\s+esperados|ganancias\s+esperadas"),
    ),
    senales_parciales=(
        senal("mencion_beneficio_generico", r"beneficio|mejora|ganancia"),
    ),
)

GR_D02_CTRL_REVISION = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-CTRL-REVISION",
        nombre="Control y plan de revision de impactos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CONTROL,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si existe un plan de revision y control para mitigar impactos adversos."
        ),
        criterios=("D02-C6",),
        prioridad_base=PrioridadDocumental.ALTA,
    ),
    senales_explicitas=(
        senal("plan_revision", r"plan\s+de\s+revision|control\s+de\s+impactos"),
    ),
    senales_parciales=(
        senal("mencion_revision_generico", r"revision|monitoreo|control"),
    ),
)

GR_D02_RESP_ACTORES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-RESP-ACTORES",
        nombre="Responsabilidad sobre accion y remedios",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.RESPONSABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se asignan responsabilidades por acciones y remedios ante impactos."
        ),
        criterios=("D02-C7",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal("responsabilidad_asignada", r"responsabilidad[s]?\s+asignad[oa]s?|responsables?\s+designad[oa]s"),
    ),
    senales_parciales=(
        senal("mencion_responsable_generico", r"responsable|remedio|accion\s+correctiva"),
    ),
)

GR_D02_QUAL_IMPACTO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-QUAL-IMPACTO",
        nombre="Calidad documental del analisis de impacto",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CALIDAD_DOCUMENTAL,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si el analisis de impacto es verificable y basado en evidencia."
        ),
        criterios=("D02-C8",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal("impacto_verificable", r"impacto\s+verificable|evidencia\s+de\s+impacto"),
    ),
    senales_parciales=(
        senal("mencion_calidad_impacto", r"verificable|evidencia|documentado"),
    ),
)

GUARDRAILS_D02 = (
    GR_D02_CONTEXTO,
    GR_D02_PRES_ACTORES,
    GR_D02_DELIM_INDIRECTOS,
    GR_D02_DELIM_VULNERABLES,
    GR_D02_VERIF_IMPACTOS,
    GR_D02_VERIF_BENEFICIOS,
    GR_D02_CTRL_REVISION,
    GR_D02_RESP_ACTORES,
    GR_D02_QUAL_IMPACTO,
)

GUARDRAILS_D01_D02 = GUARDRAILS_D01 + GUARDRAILS_D02
