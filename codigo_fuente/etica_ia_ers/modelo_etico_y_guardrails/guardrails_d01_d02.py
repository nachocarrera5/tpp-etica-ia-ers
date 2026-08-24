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
        nombre="Presencia del proposito del sistema",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.PRESENCIA,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si la ERS identifica el objetivo o problema que el "
            "sistema busca resolver."
        ),
        criterios=("D01-C1",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "proposito_con_resultado",
            r"(?:objetivo|proposito|finalidad)\s+(?:principal\s+)?"
            r"(?:del\s+sistema\s+)?(?:es|consiste\s+en|sera).{0,90}"
            r"(?:resolver|asistir|priorizar|recomendar|detectar|clasificar|"
            r"predecir|evaluar|optimizar|reducir|mejorar)",
        ),
        senal(
            "problema_y_resultado_esperado",
            r"(?:problema\s+a\s+resolver|resultado\s+esperado).{0,90}\w+",
        ),
    ),
    senales_parciales=(
        senal("mencion_proposito", r"(?:objetivo|proposito|finalidad)\s+del\s+sistema"),
        senal(
            "comportamiento_orientado_a_finalidad",
            r"el\s+sistema\s+(?:debera\s+)?(?:asistir(?:a)?|priorizar(?:a)?|"
            r"recomendar(?:a)?|detectar(?:a)?|clasificar(?:a)?|"
            r"predecir(?:a)?|evaluar(?:a)?|optimizar(?:a)?)",
        ),
    ),
)


GR_D01_DELIM_ALCANCE = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-DELIM-ALCANCE",
        nombre="Delimitacion del dominio y alcance operativo",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se delimita el dominio, contexto institucional o "
            "entorno operativo del sistema."
        ),
        criterios=("D01-C2",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "dominio_o_entorno_definido",
            r"(?:dominio|contexto|entorno|sector|ambito)\s+"
            r"(?:de\s+aplicacion|institucional|operativo|organizacional|"
            r"de\s+uso).{0,70}\w+",
        ),
        senal(
            "area_de_aplicacion_concreta",
            r"(?:solicitudes\s+internas\s+de\s+\w+|"
            r"(?:en|para)\s+(?:salud|credito|empleo|educacion|justicia|"
            r"soporte\s+tecnico|diagnostico\s+medico|gestion\s+publica))",
        ),
    ),
    senales_parciales=(
        senal("mencion_alcance", r"alcance\s+(?:del\s+)?sistema"),
        senal("mencion_contexto", r"contexto\s+(?:operativo|de\s+uso)"),
        senal("mencion_dominio", r"dominio\s+(?:de\s+aplicacion)?"),
    ),
)


GR_D01_DELIM_USOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-DELIM-USOS",
        nombre="Delimitacion de usos previstos y prohibidos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se documentan usos previstos y usos no previstos "
            "o prohibidos."
        ),
        criterios=("D01-C4", "D01-C5"),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "uso_prohibido_con_finalidad",
            r"(?:no\s+se\s+(?:usara|utilizara|empleara)|queda\s+prohibid[oa]|"
            r"no\s+estara\s+permitido).{0,90}(?:para|en)\s+\w+",
        ),
        senal(
            "uso_previsto_delimitado",
            r"(?:uso[s]?\s+previsto[s]?|solo\s+se\s+(?:usara|utilizara)|"
            r"se\s+utilizara\s+exclusivamente).{0,90}\w+",
        ),
        senal("fuera_de_alcance", r"fuera\s+de\s+alcance.{0,80}\w+"),
    ),
    senales_parciales=(
        senal("mencion_uso_previsto", r"uso[s]?\s+(?:previsto[s]?|permitido[s]?)"),
        senal("mencion_restriccion_uso", r"restriccion(?:es)?\s+de\s+uso"),
    ),
)


GR_D01_DELIM_ACTORES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-DELIM-ACTORES",
        nombre="Delimitacion de usuarios y actores principales",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se identifican usuarios o actores principales que "
            "operaran o interactuaran con el sistema."
        ),
        criterios=("D01-C3",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "actores_principales_definidos",
            r"(?:usuarios?|actores?|roles?)\s+(?:principales|autorizados|"
            r"operativos).{0,70}\w+",
        ),
        senal(
            "rol_que_opera_el_sistema",
            r"(?:sera\s+(?:utilizado|operado)\s+por|"
            r"(?:analistas?|profesionales?|operadores?|administradores?)"
            r".{0,35}(?:utilizaran|operaran|interactuaran|revisaran))",
        ),
    ),
    senales_parciales=(
        senal("mencion_usuarios", r"usuarios?\s+(?:del\s+)?sistema"),
        senal("mencion_actores", r"actores?\s+(?:del\s+)?sistema"),
        senal("mencion_roles", r"roles?\s+(?:del\s+)?sistema"),
    ),
)


GR_D01_VERIF_SUPUESTOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-VERIF-SUPUESTOS",
        nombre="Verificabilidad de supuestos operativos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si se documentan supuestos o condiciones previas "
            "necesarias para el funcionamiento."
        ),
        criterios=("D01-C6",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "supuesto_con_condicion",
            r"(?:se\s+asume\s+que|bajo\s+el\s+supuesto\s+de|"
            r"condicion\s+previa|requiere\s+que|siempre\s+que).{0,90}\w+",
        ),
        senal(
            "supuestos_operativos_documentados",
            r"supuestos?\s+(?:operativos?|del\s+contexto).{0,70}\w+",
        ),
    ),
    senales_parciales=(
        senal("mencion_supuesto", r"supuestos?\s+(?:del\s+)?sistema"),
    ),
)


GR_D01_VERIF_LIMITACIONES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-VERIF-LIMITACIONES",
        nombre="Verificabilidad de limitaciones conocidas",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D01,),
        descripcion="Verifica si se reconocen limitaciones conocidas del sistema.",
        criterios=("D01-C7",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "limitacion_concreta",
            r"(?:limitaciones?\s+conocidas?|limitado\s+a|solo\s+funciona|"
            r"no\s+(?:podra|puede|garantiza|reemplaza|admite)).{0,90}\w+",
        ),
        senal(
            "limite_operativo",
            r"limites?\s+(?:operativos?|tecnicos?|de\s+datos|del\s+dominio)"
            r".{0,70}\w+",
        ),
    ),
    senales_parciales=(
        senal("mencion_limitacion", r"limitaciones?\s+(?:del\s+)?sistema"),
    ),
)


GR_D01_QUAL_PROPOSITO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D01-QUAL-PROPOSITO",
        nombre="Calidad documental y proporcionalidad del proposito",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CALIDAD_DOCUMENTAL,
        dimensiones=(DimensionEtica.D01,),
        descripcion=(
            "Verifica si el proposito tiene criterios verificables o "
            "justifica por que corresponde utilizar IA."
        ),
        criterios=("D01-C1", "D01-C8"),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "proposito_cuantificado",
            r"(?:objetivo|proposito|resultado\s+esperado|criterio\s+de\s+exito)"
            r".{0,90}\d+(?:[.,]\d+)?\s*%",
        ),
        senal(
            "uso_ia_justificado",
            r"(?:uso|utilizacion)\s+de\s+(?:ia|inteligencia\s+artificial)"
            r".{0,80}(?:se\s+justifica|es\s+(?:adecuado|necesario)|"
            r"debido\s+a|porque)",
        ),
    ),
    senales_parciales=(
        senal("mencion_objetivo_medible", r"objetivo[s]?\s+medibles?"),
        senal("mencion_uso_ia", r"uso\s+de\s+(?:ia|inteligencia\s+artificial)"),
    ),
)


GUARDRAILS_D01: Tuple[GuardrailLexico, ...] = (
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
        nombre="Presencia de usuarios, operadores y afectados",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.PRESENCIA,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si la ERS identifica quienes interactuan con el sistema "
            "o se ven afectados por el."
        ),
        criterios=("D02-C1", "D02-C2", "D02-C3"),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "actores_concretos_identificados",
            r"(?:usuarios?|operadores?|responsables?|afectados?)\s+"
            r"(?:directos|principales|internos|indirectos).{0,70}\w+",
        ),
        senal(
            "rol_usuario_definido",
            r"(?:sera\s+(?:utilizado|operado)\s+por|"
            r"(?:analistas?|profesionales?|operadores?|administradores?)"
            r".{0,35}(?:utilizaran|operaran|supervisaran))",
        ),
    ),
    senales_parciales=(
        senal("mencion_usuario", r"usuarios?\s+(?:finales|del\s+sistema)"),
        senal("mencion_afectados", r"personas?\s+afectadas?|afectados?"),
        senal("mencion_stakeholders", r"stakeholders?|partes?\s+interesadas"),
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
            "Verifica si se identifican personas o grupos que reciben "
            "consecuencias sin interactuar directamente con el sistema."
        ),
        criterios=("D02-C3",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "afectados_indirectos_identificados",
            r"(?:afectados?|personas?|grupos?)\s+indirectos?.{0,70}\w+",
        ),
        senal(
            "terceros_con_consecuencias",
            r"terceros?.{0,60}(?:afectados?|consecuencias?|impactos?|"
            r"decisiones?)",
        ),
    ),
    senales_parciales=(
        senal("mencion_indirectos", r"afectados?\s+indirectos?"),
        senal("mencion_externalidad", r"externalidades?"),
        senal("mencion_terceros", r"terceros?\s+afectados?"),
    ),
)


GR_D02_DELIM_VULNERABLES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-DELIM-VULNERABLES",
        nombre="Delimitacion de grupos vulnerables o expuestos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se identifican grupos con mayor exposicion al "
            "riesgo o condiciones de vulnerabilidad."
        ),
        criterios=("D02-C4",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "grupo_vulnerable_identificado",
            r"(?:grupos?|personas?|poblaciones?)\s+(?:vulnerables?|"
            r"con\s+mayor\s+(?:exposicion|riesgo)).{0,70}\w+",
        ),
        senal(
            "grupo_con_riesgo_especifico",
            r"grupos?\s+con\s+\w+(?:\s+\w+){0,5}.{0,45}"
            r"(?:riesgo|exclusion|discriminacion|perjuicio)",
        ),
        senal(
            "riesgo_en_grupo_especifico",
            r"(?:riesgo|exclusion|discriminacion|perjuicio).{0,50}"
            r"grupos?\s+con\s+\w+(?:\s+\w+){0,5}",
        ),
    ),
    senales_parciales=(
        senal("mencion_vulnerabilidad", r"(?:grupo[s]?\s+)?vulnerables?"),
        senal("mencion_exposicion", r"mayor\s+exposicion\s+al\s+riesgo"),
    ),
)


GR_D02_VERIF_IMPACTOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-VERIF-IMPACTOS",
        nombre="Verificabilidad de impactos negativos previsibles",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se documentan impactos negativos previsibles con "
            "destinatarios concretos."
        ),
        criterios=("D02-C6",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "impacto_negativo_con_destinatario",
            r"(?:riesgo\s+de|dano|exclusion|perjuicio|impacto\s+negativo|"
            r"consecuencia\s+adversa).{0,70}(?:usuarios?|solicitantes?|"
            r"personas?|grupos?|comunidades?|trabajadores?|pacientes?)",
        ),
        senal(
            "destinatario_con_impacto_negativo",
            r"(?:usuarios?|solicitantes?|personas?|grupos?|comunidades?|"
            r"trabajadores?|pacientes?).{0,70}(?:riesgo|dano|exclusion|"
            r"perjuicio|impacto\s+negativo|consecuencia\s+adversa)",
        ),
    ),
    senales_parciales=(
        senal(
            "mencion_impacto_negativo",
            r"(?:impactos?\s+negativos?|riesgos?\s+sociales?|danos?\s+"
            r"previsibles?|riesgo\s+de\s+exclusion)",
        ),
    ),
)


GR_D02_VERIF_BENEFICIOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-VERIF-BENEFICIOS",
        nombre="Verificabilidad de beneficios esperados",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se indican beneficios esperados con destinatario "
            "y condicion de aplicacion."
        ),
        criterios=("D02-C5",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "beneficio_con_destinatario",
            r"(?:beneficio[s]?\s+esperados?|mejora|reduccion|aumento)"
            r".{0,70}(?:para|a)\s+(?:los?\s+|las\s+)?(?:usuarios?|"
            r"solicitantes?|personas?|grupos?|comunidades?|trabajadores?|"
            r"pacientes?)",
        ),
        senal(
            "destinatario_con_beneficio_cuantificado",
            r"(?:usuarios?|solicitantes?|personas?|grupos?|comunidades?|"
            r"trabajadores?|pacientes?).{0,70}\d+(?:[.,]\d+)?\s*%"
            r".{0,40}(?:mejora|reduccion|aumento|beneficio)",
        ),
    ),
    senales_parciales=(
        senal("mencion_beneficio", r"beneficios?\s+esperados?"),
        senal("mencion_mejora", r"mejora\s+para\s+(?:los\s+)?usuarios?"),
    ),
)


GR_D02_CTRL_REVISION = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-CTRL-REVISION",
        nombre="Control de impactos no anticipados",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CONTROL,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se preven mecanismos para detectar y atender "
            "impactos no anticipados."
        ),
        criterios=("D02-C7",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "mecanismo_ante_impacto_no_previsto",
            r"(?:si|cuando|en\s+caso\s+de).{0,60}"
            r"(?:impactos?|consecuencias?)\s+no\s+(?:previstos?|"
            r"anticipadas?).{0,90}(?:revisara|registrara|atendera|"
            r"investigara|corregira)",
        ),
        senal(
            "revision_periodica_de_impactos",
            r"(?:revision|monitoreo)\s+(?:periodica|continuo).{0,60}"
            r"(?:impactos?|consecuencias?|afectados?)",
        ),
    ),
    senales_parciales=(
        senal(
            "mencion_revision_impactos",
            r"(?:revision|monitoreo|control)\s+de\s+(?:impactos?|"
            r"consecuencias?)",
        ),
    ),
)


GR_D02_RESP_ACTORES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D02-RESP-ACTORES",
        nombre="Responsabilidad sobre afectados e impactos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.RESPONSABILIDAD,
        dimensiones=(DimensionEtica.D02,),
        descripcion=(
            "Verifica si se asigna un responsable de gestionar la relacion "
            "con afectados o revisar impactos."
        ),
        criterios=("D02-C2", "D02-C7"),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "responsable_con_accion_sobre_impactos",
            r"(?:comite|equipo|responsable|rol|area).{0,45}"
            r"(?:revisara|gestionara|atendera|investigara|respondera).{0,60}"
            r"(?:impactos?|afectados?|reclamos?|consecuencias?)",
        ),
        senal(
            "responsable_de_relacion_con_afectados",
            r"responsable\s+(?:designado\s+)?(?:de|para).{0,45}"
            r"(?:afectados?|impactos?|reclamos?|consecuencias?)",
        ),
    ),
    senales_parciales=(
        senal(
            "mencion_responsable_impactos",
            r"responsable\s+(?:de|para)\s+(?:la\s+)?revision\s+de\s+impactos?",
        ),
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
            "Verifica si impactos y beneficios tienen destinatario, "
            "condicion o mecanismo verificable."
        ),
        criterios=("D02-C5", "D02-C6", "D02-C8"),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "impacto_con_destinatario_y_condicion",
            r"(?:impacto|riesgo|beneficio).{0,60}(?:sobre|para|en)\s+"
            r"(?:usuarios?|solicitantes?|personas?|grupos?|comunidades?|"
            r"trabajadores?|pacientes?).{0,90}(?:si|cuando|mediante|"
            r"mecanismo|revision|umbral|con\s+\w+(?:\s+\w+){0,4}\s+"
            r"limitad[oa])",
        ),
        senal(
            "asimetria_y_mecanismo",
            r"(?:asimetria\s+de\s+poder|relacion\s+de\s+dependencia|"
            r"capacidad\s+de\s+reclamo|posibilidad\s+de\s+impugnacion)"
            r".{0,90}(?:mecanismo|canal|revision|reclamo|impugnacion)",
        ),
    ),
    senales_parciales=(
        senal(
            "mencion_analisis_impacto",
            r"(?:analisis|evaluacion)\s+de\s+impacto(?:s)?",
        ),
        senal("mencion_asimetria", r"asimetria\s+de\s+poder"),
    ),
)


GUARDRAILS_D02: Tuple[GuardrailLexico, ...] = (
    GR_D02_PRES_ACTORES,
    GR_D02_DELIM_INDIRECTOS,
    GR_D02_DELIM_VULNERABLES,
    GR_D02_VERIF_IMPACTOS,
    GR_D02_VERIF_BENEFICIOS,
    GR_D02_CTRL_REVISION,
    GR_D02_RESP_ACTORES,
    GR_D02_QUAL_IMPACTO,
)


GUARDRAILS_D01_D02: Tuple[GuardrailLexico, ...] = (
    GUARDRAILS_D01 + GUARDRAILS_D02
)
