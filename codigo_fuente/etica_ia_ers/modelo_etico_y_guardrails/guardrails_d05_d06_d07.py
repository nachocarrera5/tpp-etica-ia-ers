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


def _crear_guardrail(
    codigo: str,
    nombre: str,
    dimension: DimensionEtica,
    familia: FamiliaGuardrail,
    criterios: Tuple[str, ...],
    descripcion: str,
    explicitas: Tuple[Tuple[str, str], ...],
    parciales: Tuple[Tuple[str, str], ...],
    prioridad: PrioridadDocumental = PrioridadDocumental.MEDIA,
) -> GuardrailLexico:
    return GuardrailLexico(
        definicion=DefinicionGuardrail(
            codigo=codigo,
            nombre=nombre,
            version=1,
            estado=EstadoGuardrail.ACTIVA,
            familia=familia,
            dimensiones=(dimension,),
            descripcion=descripcion,
            criterios=criterios,
            prioridad_base=prioridad,
            requiere_revision_por_defecto=True,
        ),
        senales_explicitas=tuple(senal(nombre_senal, expresion) for nombre_senal, expresion in explicitas),
        senales_parciales=tuple(senal(nombre_senal, expresion) for nombre_senal, expresion in parciales),
    )


# D05 - Transparencia
GR_D05_PRES_IA = _crear_guardrail(
    "GR-D05-PRES-IA",
    "Presencia de comunicacion sobre uso de IA",
    DimensionEtica.D05,
    FamiliaGuardrail.PRESENCIA,
    ("D05-C1",),
    "Verifica si la ERS indica que debe comunicarse el uso de IA o automatizacion.",
    (("uso_ia_comunicado", r"informar\w*\s+(?:que\s+)?(?:se\s+)?usa\s+ia|generad[oa]\s+por\s+ia"),),
    (("mencion_transparencia", r"transparenc(?:ia|y)|transparent[ea]|uso\s+de\s+ia|automatizaci[oó]n"),),
    PrioridadDocumental.ALTA,
)

GR_D05_DELIM_DESTINATARIOS = _crear_guardrail(
    "GR-D05-DELIM-DESTINATARIOS",
    "Delimitacion de destinatarios de la informacion",
    DimensionEtica.D05,
    FamiliaGuardrail.DELIMITACION,
    ("D05-C2",),
    "Verifica si se identifica quien recibira la informacion sobre el sistema.",
    (("destinatarios_definidos", r"informar\w*\s+(?:al|a\s+los?|a\s+las?)\s+(?:usuario|operador|supervisor|responsable)"),),
    (("mencion_destinatarios", r"usuarios?|operadores?|supervisores?|responsables?"),),
)

GR_D05_DELIM_CONTENIDO = _crear_guardrail(
    "GR-D05-DELIM-CONTENIDO",
    "Delimitacion del contenido comunicado",
    DimensionEtica.D05,
    FamiliaGuardrail.DELIMITACION,
    ("D05-C3",),
    "Verifica si se define la informacion minima que debe comunicarse.",
    (("contenido_minimo", r"informar\w*\s+(?:sobre|acerca\s+de)\s+(?:la\s+)?(?:finalidad|funcionamiento|limites?|condiciones)"),),
    (("mencion_informacion_clara", r"informaci[oó]n\s+clara|contenido\s+m[ií]nimo"),),
)

GR_D05_VERIF_CANAL = _crear_guardrail(
    "GR-D05-VERIF-CANAL",
    "Verificabilidad del momento y canal de comunicacion",
    DimensionEtica.D05,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D05-C4",),
    "Verifica si se define cuando y por que canal se comunica la informacion.",
    (("momento_y_canal", r"(?:antes|cuando|al)\s+[^.]{0,80}(?:informar|comunicar)|(?:pantalla|correo|notificaci[oó]n|interfaz)\s+de\s+(?:informaci[oó]n|aviso)"),),
    (("mencion_comunicacion", r"comunicar|informar|notificar"),),
)

GR_D05_VERIF_LIMITES = _crear_guardrail(
    "GR-D05-VERIF-LIMITES",
    "Verificabilidad de limites y advertencias comunicados",
    DimensionEtica.D05,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D05-C5", "D05-C6"),
    "Verifica si se documentan limites, incertidumbres o advertencias que deben comunicarse.",
    (("limites_y_advertencias", r"(?:informar\w*\s+(?:sus\s+)?|incluyendo\s+(?:sus\s+)?)limit(?:e|es|aciones)|advertir\w*\s+(?:sobre|la)\s+(?:incertidumbre|errores?)"),),
    (("mencion_limites", r"limit(?:e|es|aciones)|advertencias?|incertidumbre|errores?\s+posibles"),),
    PrioridadDocumental.ALTA,
)

GR_D05_RESP_ACTUALIZACION = _crear_guardrail(
    "GR-D05-RESP-ACTUALIZACION",
    "Responsabilidad de actualizacion de la informacion",
    DimensionEtica.D05,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D05-C10",),
    "Verifica si se asigna responsable o condicion para mantener actualizada la informacion comunicada.",
    (("informacion_actualizada", r"responsable\w*\s+(?:de\s+)?actualizar|actualizar\w*\s+(?:la\s+)?informaci[oó]n"),),
    (("mencion_actualizacion", r"actualizaci[oó]n\s+de\s+(?:la\s+)?informaci[oó]n"),),
)

GR_D05_QUAL_DECLARATIVO = _crear_guardrail(
    "GR-D05-QUAL-DECLARATIVO",
    "Calidad documental de la transparencia",
    DimensionEtica.D05,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D05-C3", "D05-C5", "D05-C6"),
    "Verifica si la transparencia aparece como evidencia verificable y no solo como declaracion general.",
    (("transparencia_verificable", r"transparencia\s+(?:verificable|documentada)|informaci[oó]n\s+m[ií]nima\s+definida"),),
    (("transparencia_declarativa", r"transparente|comunicaci[oó]n\s+adecuada"),),
)

GUARDRAILS_D05: Tuple[GuardrailLexico, ...] = (
    GR_D05_PRES_IA,
    GR_D05_DELIM_DESTINATARIOS,
    GR_D05_DELIM_CONTENIDO,
    GR_D05_VERIF_CANAL,
    GR_D05_VERIF_LIMITES,
    GR_D05_RESP_ACTUALIZACION,
    GR_D05_QUAL_DECLARATIVO,
)


# D06 - Explicabilidad e interpretabilidad
GR_D06_PRES_EXPLICACION = _crear_guardrail(
    "GR-D06-PRES-EXPLICACION",
    "Presencia de explicaciones de salidas",
    DimensionEtica.D06,
    FamiliaGuardrail.PRESENCIA,
    ("D06-C1",),
    "Verifica si la ERS contempla explicaciones o justificaciones de salidas relevantes.",
    (("explicacion_de_salida", r"explicaci[oó]n\w*\s+(?:de\s+(?:la\s+)?(?:recomendaci[oó]n|decisi[oó]n|salida)|para\s+(?:el|la|los|las)\s+(?:usuario|operador|supervisor|revisor))"),),
    (("mencion_explicabilidad", r"explicab(?:le|ilidad)|explicaciones?\s+adecuadas?|justificaci[oó]n|interpretaci[oó]n"),),
    PrioridadDocumental.ALTA,
)

GR_D06_DELIM_SALIDAS = _crear_guardrail(
    "GR-D06-DELIM-SALIDAS",
    "Delimitacion de salidas que requieren explicacion",
    DimensionEtica.D06,
    FamiliaGuardrail.DELIMITACION,
    ("D06-C1",),
    "Verifica si se identifican las salidas que requieren explicacion.",
    (("salidas_identificadas", r"(?:decisiones?|recomendaciones?|salidas?)\s+(?:que\s+)?(?:deber[aá]n?|requieren?)\s+(?:ser\s+)?explicad"),),
    (("mencion_salida_explicable", r"decisiones?|recomendaciones?|salidas?"),),
)

GR_D06_DELIM_DESTINATARIOS = _crear_guardrail(
    "GR-D06-DELIM-DESTINATARIOS",
    "Delimitacion de destinatarios de explicaciones",
    DimensionEtica.D06,
    FamiliaGuardrail.DELIMITACION,
    ("D06-C2",),
    "Verifica si se identifican los destinatarios de las explicaciones.",
    (("destinatario_explicacion", r"explicaci[oó]n\w*\s+(?:para|al|a\s+los?|a\s+las?)\s+(?:usuario|operador|supervisor|revisor|afectado)"),),
    (("mencion_receptor_explicacion", r"explicaci[oó]n\w*|usuarios?|operadores?|supervisores?|revisores?"),),
)

GR_D06_VERIF_FORMATO = _crear_guardrail(
    "GR-D06-VERIF-FORMATO",
    "Verificabilidad del formato y detalle de la explicacion",
    DimensionEtica.D06,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D06-C4", "D06-C5", "D06-C6", "D06-C7"),
    "Verifica si se define el formato, contenido, nivel de detalle o factores de la explicacion.",
    (("formato_explicacion", r"(?:factores?|razones?|criterios?)\s+(?:principales|considerados)|nivel\s+de\s+detalle|formato\s+(?:de\s+)?(?:texto|explicaci[oó]n)"),),
    (("mencion_formato_explicacion", r"factores?|razones?|criterios?|formato|detalle"),),
)

GR_D06_VERIF_UTILIDAD = _crear_guardrail(
    "GR-D06-VERIF-UTILIDAD",
    "Verificabilidad de la utilidad de la explicacion",
    DimensionEtica.D06,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D06-C10",),
    "Verifica si se indica como se revisara que la explicacion sea util para su destinatario.",
    (("utilidad_revisada", r"revisar\w*\s+(?:la\s+)?utilidad|validar\w*\s+(?:la\s+)?utilidad|explicaci[oó]n\w*\s+[uú]til"),),
    (("mencion_utilidad", r"utilidad|suficiencia|adecuada"),),
)

GR_D06_CTRL_REVISION = _crear_guardrail(
    "GR-D06-CTRL-REVISION",
    "Control de uso de explicaciones para revision",
    DimensionEtica.D06,
    FamiliaGuardrail.CONTROL,
    ("D06-C9",),
    "Verifica si la explicacion puede usarse para revision, reclamo o analisis posterior.",
    (("explicacion_para_revision", r"(?:explicaci[oó]n\w*[^.]{0,100}(?:revisi[oó]n|reclamo|an[aá]lisis)|(?:usar|utilizar)\w*\s+(?:la\s+)?(?:explicaci[oó]n|explicaciones?)\s+para\s+(?:la\s+)?(?:revisi[oó]n|reclamo|an[aá]lisis))"),),
    (("mencion_revision_explicacion", r"revisi[oó]n|reclamo|an[aá]lisis\s+posterior"),),
)

GR_D06_RESP_EXPLICACION = _crear_guardrail(
    "GR-D06-RESP-EXPLICACION",
    "Responsabilidad sobre las explicaciones",
    DimensionEtica.D06,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D06-C10",),
    "Verifica si se asigna responsable de revisar o validar explicaciones.",
    (("responsable_explicaciones", r"responsable\w*\s+(?:de\s+)?(?:revisar|validar)\s+(?:la\s+)?(?:utilidad|explicaci[oó]n)"),),
    (("mencion_responsable_explicacion", r"responsable\w*|validar\w*\s+explicaci[oó]n"),),
)

GR_D06_QUAL_DECLARATIVO = _crear_guardrail(
    "GR-D06-QUAL-DECLARATIVO",
    "Calidad documental de la explicabilidad",
    DimensionEtica.D06,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D06-C4", "D06-C8"),
    "Verifica si la explicabilidad aparece como evidencia verificable y no solo como aspiracion.",
    (("explicabilidad_verificable", r"explicaci[oó]n\w*\s+(?:definida|documentada)|criterios?\s+de\s+explicabilidad"),),
    (("explicabilidad_declarativa", r"explicable|explicaciones?\s+adecuadas?"),),
)

GUARDRAILS_D06: Tuple[GuardrailLexico, ...] = (
    GR_D06_PRES_EXPLICACION,
    GR_D06_DELIM_SALIDAS,
    GR_D06_DELIM_DESTINATARIOS,
    GR_D06_VERIF_FORMATO,
    GR_D06_VERIF_UTILIDAD,
    GR_D06_CTRL_REVISION,
    GR_D06_RESP_EXPLICACION,
    GR_D06_QUAL_DECLARATIVO,
)


# D07 - Supervision humana
GR_D07_PRES_HUMANO = _crear_guardrail(
    "GR-D07-PRES-HUMANO",
    "Presencia de supervision humana",
    DimensionEtica.D07,
    FamiliaGuardrail.PRESENCIA,
    ("D07-C1",),
    "Verifica si la ERS contempla supervision o intervencion humana.",
    (("supervision_humana", r"supervisi[oó]n\s+humana|intervenci[oó]n\s+humana|supervisor\s+autorizado"),),
    (("mencion_revision_humana", r"revisi[oó]n\s+humana|personal\s+autorizado"),),
    PrioridadDocumental.ALTA,
)

GR_D07_DELIM_DECISIONES = _crear_guardrail(
    "GR-D07-DELIM-DECISIONES",
    "Delimitacion de decisiones supervisadas",
    DimensionEtica.D07,
    FamiliaGuardrail.DELIMITACION,
    ("D07-C1",),
    "Verifica si se identifican decisiones o salidas sujetas a supervision.",
    (("decisiones_supervisadas", r"(?:decisiones?|recomendaciones?|salidas?)\s+(?:deber[aá]n?|ser[aá]n?)\s+(?:ser\s+)?revisad"),),
    (("mencion_decisiones", r"decisiones?|recomendaciones?|salidas?"),),
)

GR_D07_DELIM_ROLES = _crear_guardrail(
    "GR-D07-DELIM-ROLES",
    "Delimitacion de roles de supervision",
    DimensionEtica.D07,
    FamiliaGuardrail.DELIMITACION,
    ("D07-C2",),
    "Verifica si se identifican responsables humanos de revisar o intervenir.",
    (("rol_supervisor", r"supervisor\w*\s+(?:autorizad[oa]|responsable)|personal\s+autorizado"),),
    (("mencion_rol_supervision", r"supervisor\w*|personal\s+autorizado|responsable\w*"),),
)

GR_D07_CTRL_INTERVENCION = _crear_guardrail(
    "GR-D07-CTRL-INTERVENCION",
    "Control de autoridad de intervencion",
    DimensionEtica.D07,
    FamiliaGuardrail.CONTROL,
    ("D07-C3",),
    "Verifica si existe capacidad documentada de aprobar, rechazar, corregir, pausar o escalar resultados.",
    (("autoridad_intervencion", r"(?:aprobar|rechazar|corregir|pausar|escalar)\w*(?:,|\s+o\s+)+(?:aprobar|rechazar|corregir|pausar|escalar)\w*"),),
    (("mencion_intervencion", r"aprobar|rechazar|corregir|pausar|escalar"),),
    PrioridadDocumental.ALTA,
)

GR_D07_VERIF_ACTIVACION = _crear_guardrail(
    "GR-D07-VERIF-ACTIVACION",
    "Verificabilidad de condiciones de activacion",
    DimensionEtica.D07,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D07-C4",),
    "Verifica si se definen las condiciones que activan la revision humana.",
    (("condicion_revision", r"(?:si|cuando|ante)\s+(?:la\s+)?(?:diferencia|incertidumbre|alto\s+riesgo|riesgo)\w*[^.]{0,60}revisi[oó]n"),),
    (("mencion_activacion", r"condici[oó]n\w*\s+(?:de\s+)?(?:revisi[oó]n|intervenci[oó]n)|alto\s+riesgo"),),
)

GR_D07_VERIF_PROCEDIMIENTO = _crear_guardrail(
    "GR-D07-VERIF-PROCEDIMIENTO",
    "Verificabilidad del procedimiento de revision",
    DimensionEtica.D07,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D07-C5", "D07-C6", "D07-C10"),
    "Verifica si se define un procedimiento de revision, escalamiento e informacion disponible.",
    (("procedimiento_revision", r"procedimiento\s+(?:documentado\s+)?de\s+revisi[oó]n|pasos\s+(?:para|de)\s+revisar"),),
    (("mencion_procedimiento", r"procedimiento|pasos\s+de\s+revisi[oó]n|informaci[oó]n\s+disponible"),),
)

GR_D07_RESP_REGISTRO = _crear_guardrail(
    "GR-D07-RESP-REGISTRO",
    "Responsabilidad y registro de la intervencion",
    DimensionEtica.D07,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D07-C8",),
    "Verifica si se documenta que debe registrarse de la intervencion humana.",
    (("registro_intervencion", r"registr\w*\s+(?:el\s+)?(?:motivo|decisi[oó]n|intervenci[oó]n)|registro\s+(?:de\s+la\s+)?intervenci[oó]n"),),
    (("mencion_registro", r"registrar\w*|registro\w*"),),
)

GR_D07_QUAL_DECLARATIVO = _crear_guardrail(
    "GR-D07-QUAL-DECLARATIVO",
    "Calidad documental de la supervision humana",
    DimensionEtica.D07,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D07-C2", "D07-C3", "D07-C4", "D07-C5"),
    "Verifica si la supervision humana es verificable y no solo declarativa.",
    (("supervision_verificable", r"supervisi[oó]n\s+humana\s+(?:obligatoria|definida|documentada)|revisi[oó]n\s+humana\s+obligatoria"),),
    (("supervision_declarativa", r"podr[aá]n\s+ser\s+revisad[oa]s?|supervisi[oó]n\s+humana"),),
)

GUARDRAILS_D07: Tuple[GuardrailLexico, ...] = (
    GR_D07_PRES_HUMANO,
    GR_D07_DELIM_DECISIONES,
    GR_D07_DELIM_ROLES,
    GR_D07_CTRL_INTERVENCION,
    GR_D07_VERIF_ACTIVACION,
    GR_D07_VERIF_PROCEDIMIENTO,
    GR_D07_RESP_REGISTRO,
    GR_D07_QUAL_DECLARATIVO,
)

GUARDRAILS_D05_D07: Tuple[GuardrailLexico, ...] = GUARDRAILS_D05 + GUARDRAILS_D06 + GUARDRAILS_D07