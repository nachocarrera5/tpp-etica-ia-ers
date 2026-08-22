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


GR_D03_PRES_DATOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D03-PRES-DATOS",
        nombre="Presencia de datos utilizados por el sistema",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.PRESENCIA,
        dimensiones=(DimensionEtica.D03,),
        descripcion=(
            "Verifica si la ERS identifica que datos usa el sistema de IA "
            "(D03-C1 Origen de datos, D03-C3 Categorias de datos)."
        ),
        criterios=("D03-C1", "D03-C3"),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "categorias_datos_especificas",
            r"datos\s+(?:personales|sensibles|biometricos|de\s+salud|"
            r"financieros|de\s+ubicacion|de\s+identificacion)",
        ),
        senal(
            "origen_de_datos_especifico",
            r"(?:proceden|proceder|provendran|provenir|se\s+obtendran)"
            r"\s+de\s+(?:registros|fuentes|bases\s+de\s+datos)\s+"
            r"(?:autorizad[oa]s|oficiales|internas)",
        ),
    ),
    senales_parciales=(
        senal("mencion_datos_usuario", r"datos\s+del\s+usuario"),
        senal("mencion_informacion_usuario", r"informacion\s+del\s+usuario"),
        senal("mencion_generica_datos", r"(?:usar[a]?|utilizar[a]?)\s+datos"),
    ),
)

GR_D03_DELIM_FINALIDAD = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D03-DELIM-FINALIDAD",
        nombre="Delimitacion de la finalidad de uso de los datos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D03,),
        descripcion=(
            "Verifica si la finalidad de uso de los datos esta definida y "
            "vinculada al proposito del sistema (D03-C2 Finalidad de uso, "
            "D03-C4 Minimizacion)."
        ),
        criterios=("D03-C2", "D03-C4"),
        prioridad_base=PrioridadDocumental.MEDIA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "finalidad_declarada_con_limite",
            r"(?:se\s+limitaran|excluir[a]?|solo\s+se\s+usaran)\s+"
            r"(?:a\s+)?(?:variables|datos)\s+necesari[oa]s\s+"
            r"para\s+la\s+finalidad",
        ),
        senal(
            "finalidad_para_proposito",
            r"para\s+la\s+finalidad\s+declarada",
        ),
    ),
    senales_parciales=(
        senal("mencion_finalidad", r"finalidad(?:es)?\s+de\s+uso"),
        senal("mencion_proposito_datos", r"para\s+generar\s+una?\s+\w+"),
    ),
)

GR_D03_VERIF_CALIDAD = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D03-VERIF-CALIDAD",
        nombre="Verificabilidad de la calidad y representatividad de datos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D03,),
        descripcion=(
            "Verifica si se definen criterios de calidad, actualizacion o "
            "representatividad de los datos (D03-C6 Calidad y "
            "representatividad, D03-C9 Documentacion del dataset)."
        ),
        criterios=("D03-C6", "D03-C9"),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "documentacion_limitaciones",
            r"documentar[a]?\s+limitaciones\s+conocidas\s+del\s+dataset",
        ),
        senal(
            "periodo_de_datos",
            r"(?:ultimos?|periodo\s+de)\s+\d+\s+mes(?:es)?",
        ),
    ),
    senales_parciales=(
        senal("mencion_calidad", r"calidad\s+(?:de\s+los?\s+)?datos?"),
        senal("mencion_representatividad", r"representativ[oa]s?"),
        senal("mencion_actualizacion_datos", r"actualizaci[oó]n\s+de\s+datos"),
    ),
)

GR_D03_RESP_ACCESO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D03-RESP-ACCESO",
        nombre="Responsabilidad sobre el acceso a los datos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.RESPONSABILIDAD,
        dimensiones=(DimensionEtica.D03,),
        descripcion=(
            "Verifica si se indican roles o responsables con acceso a los "
            "datos (D03-C7 Acceso y seguridad)."
        ),
        criterios=("D03-C7",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "roles_autorizados_definidos",
            r"(?:roles?|responsables?)\s+autorizad[oa]s?\s+"
            r"(?:para\s+)?(?:acced|con\s+acceso)",
        ),
        senal(
            "control_de_acceso_especifico",
            r"control(?:es)?\s+de\s+acceso\s+(?:basad[oa]\s+en|por)\s+rol",
        ),
    ),
    senales_parciales=(
        senal("mencion_acceso", r"acceso\s+a\s+(?:los\s+)?datos"),
        senal("mencion_seguridad_generica", r"datos\s+(?:estaran\s+)?seguros?"),
        senal("mencion_proteccion_generica", r"datos\s+(?:estaran\s+)?protegidos?"),
    ),
)

GR_D03_CTRL_RETENCION = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D03-CTRL-RETENCION",
        nombre="Control de retencion, eliminacion y anonimizacion",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CONTROL,
        dimensiones=(DimensionEtica.D03,),
        descripcion=(
            "Verifica si se documentan retencion, eliminacion, "
            "anonimizacion o restricciones de uso (D03-C8 Retencion y "
            "eliminacion)."
        ),
        criterios=("D03-C8",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "plazo_retencion_definido",
            r"retencion\s+maxima\s+definida",
        ),
        senal(
            "plazo_numerico_retencion",
            r"(?:plazo|periodo)\s+de\s+retencion\s+de\s+\d+",
        ),
    ),
    senales_parciales=(
        senal("mencion_retencion", r"retenci[oó]n\s+de\s+datos"),
        senal("mencion_eliminacion", r"eliminaci[oó]n\s+de\s+datos"),
        senal("mencion_anonimizacion", r"anonimizaci[oó]n"),
    ),
)

GR_D03_QUAL_PRIVACIDAD = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D03-QUAL-PRIVACIDAD",
        nombre="Calidad documental de las afirmaciones sobre privacidad",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CALIDAD_DOCUMENTAL,
        dimensiones=(DimensionEtica.D03,),
        descripcion=(
            "Verifica si las afirmaciones sobre privacidad son verificables "
            "y no meramente declarativas (D03-C5 Base de uso o "
            "consentimiento, D03-C10 Trazabilidad de uso)."
        ),
        criterios=("D03-C5", "D03-C10"),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "consentimiento_explicito",
            r"consentimiento\s+(?:explicito|informado)\s+"
            r"(?:del|de\s+los?)\s+usuari[oa]s?",
        ),
        senal(
            "base_legal_definida",
            r"base\s+legal\s+(?:para|de)\s+el\s+tratamiento",
        ),
    ),
    senales_parciales=(
        senal("mencion_consentimiento", r"consentimiento"),
        senal("mencion_privacidad_generica", r"privacidad\s+de\s+los?\s+datos"),
    ),
)

GUARDRAILS_D03: Tuple[GuardrailLexico, ...] = (
    GR_D03_PRES_DATOS,
    GR_D03_DELIM_FINALIDAD,
    GR_D03_VERIF_CALIDAD,
    GR_D03_RESP_ACCESO,
    GR_D03_CTRL_RETENCION,
    GR_D03_QUAL_PRIVACIDAD,
)

GR_D04_PRES_SESGOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D04-PRES-SESGOS",
        nombre="Presencia de mencion a sesgos, equidad o trato desigual",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.PRESENCIA,
        dimensiones=(DimensionEtica.D04,),
        descripcion=(
            "Verifica si la ERS menciona sesgos, equidad, discriminacion "
            "o trato desigual (D04-C4 Riesgos de sesgo)."
        ),
        criterios=("D04-C4",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "reporte_diferenciado_por_grupo",
            r"reportar[a]?\s+(?:desempeno|falsos\s+negativos|"
            r"falsos\s+positivos)\s+por\s+grupo",
        ),
        senal(
            "umbral_diferencia_subgrupos",
            r"diferencia\s+de\s+\w+\s+entre\s+subgrupos\s+"
            r"supera\s+el?\s+umbral",
        ),
    ),
    senales_parciales=(
        senal("mencion_sesgos", r"sesgos?"),
        senal("mencion_equidad", r"equidad|equitativ[oa]s?"),
        senal("mencion_discriminacion", r"discriminaci[oó]n|discriminatori[oa]s?"),
        senal("mencion_trato_justo", r"result?ados?\s+justos?|trato\s+desigual"),
    ),
)

GR_D04_DELIM_GRUPOS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D04-DELIM-GRUPOS",
        nombre="Delimitacion de grupos o subpoblaciones relevantes",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D04,),
        descripcion=(
            "Verifica si se identifican grupos o subpoblaciones relevantes "
            "(D04-C1 Grupos afectados)."
        ),
        criterios=("D04-C1",),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "desempeno_por_grupo_especifico",
            r"desempeno\s+por\s+grupo\s+(?:etario|de\s+edad)\s+y\s+genero",
        ),
        senal(
            "subgrupos_definidos",
            r"por\s+(?:subgrupos?|subpoblaci(?:on|ones))\s+"
            r"(?:etari[oa]s?|de\s+genero|relevantes?)",
        ),
    ),
    senales_parciales=(
        senal("mencion_grupos", r"grupos?\s+(?:afectad[oa]s|vulnerables?)"),
        senal("mencion_subpoblacion", r"subpoblaci(?:on|ones)"),
        senal("mencion_usuarios_afectados", r"usuarios?\s+afectad[oa]s"),
    ),
)

GR_D04_DELIM_PROXIES = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D04-DELIM-PROXIES",
        nombre="Delimitacion de atributos sensibles y variables proxy",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.DELIMITACION,
        dimensiones=(DimensionEtica.D04,),
        descripcion=(
            "Verifica si se revisan atributos sensibles o variables proxy "
            "(D04-C2 Atributos sensibles, D04-C3 Variables proxy)."
        ),
        criterios=("D04-C2", "D04-C3"),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "atributo_sensible_explicito",
            r"atributos?\s+(?:sensibles?|protegid[oa]s?)\s+"
            r"(?:como|tales\s+como|incluyen)",
        ),
        senal("variable_proxy_identificada", r"variables?\s+proxy"),
    ),
    senales_parciales=(
        senal("mencion_atributos_sensibles", r"atributos?\s+sensibles?"),
        senal("mencion_atributos_protegidos", r"atributos?\s+protegid[oa]s?"),
    ),
)

GR_D04_VERIF_METRICAS = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D04-VERIF-METRICAS",
        nombre="Verificabilidad de metricas y pruebas de equidad",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        dimensiones=(DimensionEtica.D04,),
        descripcion=(
            "Verifica si se definen metricas, pruebas o criterios de "
            "comparacion para equidad (D04-C5 Metricas de equidad, "
            "D04-C6 Pruebas por subpoblacion)."
        ),
        criterios=("D04-C5", "D04-C6"),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "metrica_falsos_negativos_por_grupo",
            r"falsos\s+negativos\s+entre\s+subgrupos",
        ),
        senal(
            "prueba_por_subpoblacion_definida",
            r"prueba(?:s)?\s+por\s+subpoblaci(?:on|ones)",
        ),
    ),
    senales_parciales=(
        senal("mencion_metricas_equidad", r"m[eé]tricas?\s+de\s+equidad"),
        senal("mencion_pruebas_diferenciadas", r"evaluaci[oó]n\s+diferenciada"),
    ),
)

GR_D04_CTRL_MITIGACION = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D04-CTRL-MITIGACION",
        nombre="Control de acciones correctivas ante sesgos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CONTROL,
        dimensiones=(DimensionEtica.D04,),
        descripcion=(
            "Verifica si se preven acciones correctivas ante sesgos o "
            "diferencias de desempeno (D04-C7 Umbrales o criterios de "
            "revision, D04-C8 Acciones correctivas)."
        ),
        criterios=("D04-C7", "D04-C8"),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=True,
    ),
    senales_explicitas=(
        senal(
            "activacion_revision_por_umbral",
            r"activar[a]?\s+revision\s+(?:del\s+responsable\s+)?"
            r"(?:designado\s+)?si\s+la\s+diferencia",
        ),
        senal("umbral_definido_para_dominio", r"umbral\s+definido\s+para\s+el?\s+dominio"),
    ),
    senales_parciales=(
        senal("mencion_accion_correctiva", r"acci(?:on|ones)\s+correctiv[oa]s?"),
        senal("mencion_umbral_generico", r"umbral(?:es)?\s+de\s+revisi[oó]n"),
        senal("mencion_mitigacion", r"mitigaci[oó]n\s+de\s+sesgos?"),
    ),
)

GR_D04_RESP_REVISION = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D04-RESP-REVISION",
        nombre="Responsabilidad sobre la revision de sesgos",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.RESPONSABILIDAD,
        dimensiones=(DimensionEtica.D04,),
        descripcion=(
            "Verifica si se asigna responsable de revisar y actuar ante "
            "desviaciones (D04-C9 Responsable de revision)."
        ),
        criterios=("D04-C9",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "responsable_designado_explicito",
            r"responsable\s+designado",
        ),
        senal(
            "rol_encargado_de_revision",
            r"rol\s+(?:encargado|responsable)\s+de\s+revisar",
        ),
    ),
    senales_parciales=(
        senal("mencion_responsable_generico", r"responsable\s+de\s+(?:la\s+)?revisi[oó]n"),
    ),
)

GR_D04_QUAL_DECLARATIVO = GuardrailLexico(
    definicion=DefinicionGuardrail(
        codigo="GR-D04-QUAL-DECLARATIVO",
        nombre="Calidad documental: equidad como requisito verificable",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.CALIDAD_DOCUMENTAL,
        dimensiones=(DimensionEtica.D04,),
        descripcion=(
            "Verifica si la equidad aparece como requisito verificable y "
            "no solo como declaracion aspiracional (D04-C10 Seguimiento "
            "posterior)."
        ),
        criterios=("D04-C10",),
        prioridad_base=PrioridadDocumental.MEDIA,
    ),
    senales_explicitas=(
        senal(
            "monitoreo_periodico_definido",
            r"monitoreo\s+(?:periodico|continuo)\s+"
            r"(?:de|ante)\s+cambios?",
        ),
        senal("revision_periodica_definida", r"revisi[oó]n\s+periodica\s+"
             r"(?:de|ante)\s+cambios?\s+(?:en|de)\s+(?:los?\s+)?datos"),
    ),
    senales_parciales=(
        senal("mencion_seguimiento", r"seguimiento\s+posterior"),
        senal("mencion_monitoreo_generico", r"monitoreo"),
    ),
)

GUARDRAILS_D04: Tuple[GuardrailLexico, ...] = (
    GR_D04_PRES_SESGOS,
    GR_D04_DELIM_GRUPOS,
    GR_D04_DELIM_PROXIES,
    GR_D04_VERIF_METRICAS,
    GR_D04_CTRL_MITIGACION,
    GR_D04_RESP_REVISION,
    GR_D04_QUAL_DECLARATIVO,
)

GUARDRAILS_D03_D04: Tuple[GuardrailLexico, ...] = GUARDRAILS_D03 + GUARDRAILS_D04
