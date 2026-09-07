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


def _coocurrencia(
    primer_concepto: str,
    segundo_concepto: str,
    distancia: int = 500,
) -> str:
    return (
        rf"(?=^.{{0,{distancia}}}(?:{primer_concepto}))"
        rf"(?=^.{{0,{distancia}}}(?:{segundo_concepto}))"
        rf"^.{{0,{distancia}}}"
    )


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
        senales_explicitas=tuple(
            senal(nombre_senal, expresion)
            for nombre_senal, expresion in explicitas
        ),
        senales_parciales=tuple(
            senal(nombre_senal, expresion)
            for nombre_senal, expresion in parciales
        ),
    )


# D08 - Robustez, seguridad y fiabilidad
GR_D08_PRES_ROBUSTEZ = _crear_guardrail(
    "GR-D08-PRES-ROBUSTEZ",
    "Presencia de robustez, seguridad y fiabilidad",
    DimensionEtica.D08,
    FamiliaGuardrail.PRESENCIA,
    ("D08-C3", "D08-C4", "D08-C5"),
    (
        "Verifica si la ERS contempla condiciones concretas de robustez, "
        "seguridad o fiabilidad."
    ),
    (
        (
            "respuesta_operativa_ante_riesgo",
            _coocurrencia(
                r"(?:datos?\s+incompletos?|entradas?\s+inv[aá]lidas?|"
                r"baja\s+confianza|fallas?|degradaci[oó]n|ataques?|"
                r"acceso\s+indebido)",
                r"(?:no\s+emitir|rechazar|pausar|interrumpir|bloquear|"
                r"revisi[oó]n\s+manual|modo\s+degradado)",
            ),
        ),
    ),
    (
        (
            "robustez_declarativa",
            r"(?:sistema|modelo).{0,50}(?:robust[oa]|segur[oa]|fiable|"
            r"confiable)|(?:robustez|fiabilidad|seguridad)\s+del\s+"
            r"(?:sistema|modelo)|(?:proteger|proteccion|confidencialidad)"
            r".{0,70}datos.{0,70}cifrad\w*",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D08_VERIF_METRICAS = _crear_guardrail(
    "GR-D08-VERIF-METRICAS",
    "Verificabilidad de metricas y umbrales operativos",
    DimensionEtica.D08,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D08-C1", "D08-C2"),
    "Verifica si se definen metricas, umbrales o condiciones de aceptacion.",
    (
        (
            "metrica_con_umbral",
            _coocurrencia(
                r"(?:precisi[oó]n|recall|f1|disponibilidad|latencia|"
                r"confianza|tasa\s+de\s+error|desempe[nñ]o|"
                r"tiempo\s+de\s+respuesta|responder)",
                r"(?:\d+(?:[.,]\d+)?\s*%?|umbral\s+(?:definido|m[ií]nimo|"
                r"m[aá]ximo)|inferior\s+al\s+umbral|superior\s+al\s+umbral|"
                r"criterio\s+de\s+aceptaci[oó]n|(?:(?:menor|inferior)\s+a|"
                r"menos\s+de)\s+"
                r"(?:un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|"
                r"diez)\s+(?:segundos?|minutos?|horas?))",
            ),
        ),
    ),
    (
        (
            "metrica_sin_umbral",
            r"(?:m[eé]tricas?|indicadores?).{0,45}(?:desempe[nñ]o|"
            r"disponibilidad|precisi[oó]n|confianza|calidad)|"
            r"(?:desempe[nñ]o|disponibilidad|precisi[oó]n|confianza)"
            r".{0,45}(?:m[eé]tricas?|indicadores?)",
        ),
    ),
)

GR_D08_CTRL_FALLAS = _crear_guardrail(
    "GR-D08-CTRL-FALLAS",
    "Control ante fallas y degradacion",
    DimensionEtica.D08,
    FamiliaGuardrail.CONTROL,
    ("D08-C3", "D08-C4", "D08-C9"),
    (
        "Verifica si se documenta el comportamiento ante fallas, datos "
        "invalidos, baja confianza o degradacion."
    ),
    (
        (
            "comportamiento_ante_falla",
            _coocurrencia(
                r"(?:datos?\s+incompletos?|datos?\s+inv[aá]lidos?|"
                r"entradas?\s+fuera\s+de\s+distribuci[oó]n|fallas?|"
                r"errores?|baja\s+confianza|degradaci[oó]n)",
                r"(?:no\s+(?:deber[aá]\s+)?(?:emitir|operar|utilizar)|"
                r"rechazar|pausar|interrumpir|derivar|alertar|"
                r"revisi[oó]n\s+manual)",
            ),
        ),
    ),
    (
        (
            "falla_sin_respuesta",
            r"(?:sistema|modelo).{0,60}(?:fallas?|errores?|degradaci[oó]n|"
            r"baja\s+confianza)|(?:datos?|entradas?).{0,40}"
            r"(?:incompletos?|inv[aá]lidos?|corruptos?)",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D08_CTRL_CONTINGENCIA = _crear_guardrail(
    "GR-D08-CTRL-CONTINGENCIA",
    "Control de contingencias e interrupcion",
    DimensionEtica.D08,
    FamiliaGuardrail.CONTROL,
    ("D08-C7", "D08-C9"),
    (
        "Verifica si se preven contingencias, pausas, reversion o "
        "derivacion manual."
    ),
    (
        (
            "contingencia_definida",
            _coocurrencia(
                r"(?:falla|incidente|degradaci[oó]n|baja\s+confianza|"
                r"interrupci[oó]n|contingencia)",
                r"(?:modo\s+degradado|reversi[oó]n|rollback|pausar|"
                r"interrumpir|derivaci[oó]n\s+manual|revisi[oó]n\s+manual|"
                r"plan\s+de\s+contingencia)",
            ),
        ),
    ),
    (
        (
            "contingencia_generica",
            r"plan\s+de\s+contingencia|modo\s+degradado|"
            r"procedimiento\s+ante\s+fallas?",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D08_VERIF_MONITOREO = _crear_guardrail(
    "GR-D08-VERIF-MONITOREO",
    "Verificabilidad del monitoreo de cambios",
    DimensionEtica.D08,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D08-C6",),
    (
        "Verifica si se monitorean drift, cambios de contexto o degradacion "
        "con una condicion revisable."
    ),
    (
        (
            "monitoreo_con_condicion",
            _coocurrencia(
                r"(?:drift|cambio\s+de\s+distribuci[oó]n|cambio\s+de\s+"
                r"contexto|degradaci[oó]n\s+del\s+desempe[nñ]o)",
                r"(?:monitorear|revisar|evaluar|medir)\w*.{0,70}"
                r"(?:mensual|trimestral|semestral|anual|cada\s+\d+|umbral|"
                r"alerta|pausar)",
            ),
        ),
    ),
    (
        (
            "monitoreo_generico",
            r"(?:monitorear|revisar)\w*.{0,60}(?:drift|"
            r"cambio\s+de\s+distribuci[oó]n|degradaci[oó]n)|"
            r"monitoreo\s+(?:del\s+)?(?:modelo|desempe[nñ]o)",
        ),
    ),
)

GR_D08_RESP_INCIDENTES = _crear_guardrail(
    "GR-D08-RESP-INCIDENTES",
    "Responsabilidad y registro de incidentes",
    DimensionEtica.D08,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D08-C8", "D08-C10"),
    (
        "Verifica si se asigna un rol para revisar y registrar incidentes, "
        "alertas o interrupciones."
    ),
    (
        (
            "responsable_de_incidentes",
            _coocurrencia(
                r"(?:responsable|equipo\s+de\s+operaciones|supervisor|"
                r"administrador|rol\s+operativo)",
                r"(?:incidentes?|alertas?|degradaci[oó]n|interrupciones?)"
                r".{0,80}(?:registrar|revisar|atender|resolver|escalar)\w*|"
                r"(?:registrar|revisar|atender|resolver|escalar)\w*.{0,80}"
                r"(?:incidentes?|alertas?|degradaci[oó]n|interrupciones?)",
            ),
        ),
    ),
    (
        (
            "incidente_sin_responsabilidad_completa",
            r"(?:registro|revisi[oó]n|gesti[oó]n).{0,40}"
            r"(?:incidentes?|alertas?)|(?:responsable|equipo).{0,45}"
            r"(?:incidentes?|alertas?)",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D08_QUAL_DECLARATIVO = _crear_guardrail(
    "GR-D08-QUAL-DECLARATIVO",
    "Calidad documental de robustez y seguridad",
    DimensionEtica.D08,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D08-C1", "D08-C2", "D08-C5", "D08-C7"),
    (
        "Verifica si robustez y seguridad se documentan mediante criterios "
        "revisables y no como valores abstractos."
    ),
    (
        (
            "robustez_verificable",
            _coocurrencia(
                r"(?:robustez|seguridad|fiabilidad|sistema\s+robusto|"
                r"sistema\s+seguro|sistema\s+confiable)",
                r"(?:pruebas?|m[eé]tricas?|umbrales?|criterios?\s+de\s+"
                r"aceptaci[oó]n|contingencias?|simulaci[oó]n\s+de\s+fallas?)",
            ),
        ),
    ),
    (
        (
            "robustez_abstracta",
            r"(?:sistema|modelo).{0,45}(?:seguro|robusto|confiable|fiable)"
            r"(?:\s+y\s+(?:seguro|robusto|confiable|fiable))*",
        ),
    ),
)

GUARDRAILS_D08: Tuple[GuardrailLexico, ...] = (
    GR_D08_PRES_ROBUSTEZ,
    GR_D08_VERIF_METRICAS,
    GR_D08_CTRL_FALLAS,
    GR_D08_CTRL_CONTINGENCIA,
    GR_D08_VERIF_MONITOREO,
    GR_D08_RESP_INCIDENTES,
    GR_D08_QUAL_DECLARATIVO,
)


# D09 - Accountability y auditoria
GR_D09_PRES_RESPONSABLES = _crear_guardrail(
    "GR-D09-PRES-RESPONSABLES",
    "Presencia de responsables de decisiones y operacion",
    DimensionEtica.D09,
    FamiliaGuardrail.PRESENCIA,
    ("D09-C1", "D09-C2"),
    (
        "Verifica si la ERS asigna responsables sobre decisiones, cambios, "
        "datos, modelo u operacion."
    ),
    (
        (
            "responsabilidad_asignada",
            _coocurrencia(
                r"(?:responsable|propietario|equipo|comit[eé]|analista|"
                r"supervisor|administrador)",
                r"(?:decisi[oó]n(?:es)?|cambios?|datos?|modelo|operaci[oó]n|"
                r"auditor[ií]a).{0,70}(?:aprobar|revisar|responder|validar|"
                r"gestionar)\w*|(?:aprobar|revisar|responder|validar|"
                r"gestionar)\w*.{0,70}(?:decisi[oó]n(?:es)?|cambios?|"
                r"datos?|modelo|operaci[oó]n|auditor[ií]a)",
            ),
        ),
        (
            "responsable_en_registro_de_incidente",
            _coocurrencia(
                r"(?:responsable|propietario|equipo|comit[eé]|analista|"
                r"supervisor|administrador)",
                r"(?:incidentes?|decisi[oó]n(?:es)?|cambios?).{0,80}"
                r"(?:registrar|registrarse|registro)|(?:registrar|registro)"
                r".{0,80}(?:incidentes?|decisi[oó]n(?:es)?|cambios?)",
            ),
        ),
    ),
    (
        (
            "responsabilidad_generica",
            r"(?:accountability|rendici[oó]n\s+de\s+cuentas|"
            r"responsabilidad).{0,40}(?:sistema|modelo|decisi[oó]n(?:es)?|"
            r"operaci[oó]n)|responsables?\s+designados?",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D09_RESP_ROLES = _crear_guardrail(
    "GR-D09-RESP-ROLES",
    "Responsabilidad diferenciada por roles",
    DimensionEtica.D09,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D09-C1", "D09-C2", "D09-C6"),
    (
        "Verifica si se diferencian roles responsables por datos, modelo, "
        "operacion o auditoria."
    ),
    (
        (
            "rol_con_responsabilidad",
            r"(?:responsable\s+de\s+datos|propietario\s+del\s+modelo|"
            r"equipo\s+de\s+operaciones|comit[eé]\s+de\s+auditor[ií]a|"
            r"auditor|supervisor).{0,90}(?:aprobar|revisar|validar|"
            r"monitorear|auditar|responder|gestionar)\w*",
        ),
    ),
    (
        (
            "rol_poco_delimitado",
            _coocurrencia(
                r"(?:responsable|equipo|comit[eé]|rol)",
                r"(?:datos?|modelo|operaci[oó]n|revisi[oó]n|auditor[ií]a)",
            ),
        ),
    ),
)

GR_D09_VERIF_REGISTROS = _crear_guardrail(
    "GR-D09-VERIF-REGISTROS",
    "Verificabilidad de registros y trazabilidad",
    DimensionEtica.D09,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D09-C3", "D09-C5", "D09-C10"),
    (
        "Verifica si se definen eventos, campos y condiciones de "
        "conservacion de evidencia auditable."
    ),
    (
        (
            "registro_con_campos",
            _coocurrencia(
                r"(?:(?:registrar|registrarse|registro|trazabilidad|"
                r"log\s+de\s+auditor[ií]a).{0,80}(?:decisi[oó]n(?:es)?|"
                r"cambios?|incidentes?|salidas?|eventos?|"
                r"evaluaci[oó]n(?:es)?)|"
                r"(?:decisi[oó]n(?:es)?|cambios?|incidentes?|salidas?|"
                r"eventos?|evaluaci[oó]n(?:es)?).{0,80}"
                r"(?:registrar|registrarse|registro|"
                r"trazabilidad|log\s+de\s+auditor[ií]a))",
                r"(?:fecha|responsable|versi[oó]n|motivo|datos?\s+de\s+"
                r"entrada|variables?\s+de\s+entrada|acci[oó]n\s+tomada|"
                r"identificador)",
            ),
        ),
        (
            "conservacion_definida",
            r"(?:registros?|evidencias?|logs?).{0,70}(?:conservar|retener|"
            r"mantener)\w*.{0,40}(?:\d+\s+(?:d[ií]as|meses|a[nñ]os)|"
            r"plazo\s+definido)",
        ),
    ),
    (
        (
            "registro_generico",
            r"(?:registro|log|trazabilidad).{0,45}(?:decisi[oó]n(?:es)?|cambios?|"
            r"incidentes?|modelo)|auditor[ií]a\s+de\s+registros",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D09_VERIF_VERSIONADO = _crear_guardrail(
    "GR-D09-VERIF-VERSIONADO",
    "Verificabilidad del versionado y los cambios",
    DimensionEtica.D09,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D09-C4", "D09-C9"),
    (
        "Verifica si se documentan versiones y cambios de modelos, datos, "
        "reglas o configuraciones."
    ),
    (
        (
            "version_con_cambio_trazable",
            _coocurrencia(
                r"versi[oó]n.{0,35}(?:modelo|dataset|datos|reglas?|"
                r"criterios?|configuraci[oó]n)|(?:modelo|dataset|datos|"
                r"reglas?|criterios?|configuraci[oó]n).{0,35}versi[oó]n",
                r"(?:fecha|responsable|motivo|aprobaci[oó]n|m[eé]tricas?\s+"
                r"comparativas?|cambio)",
            ),
        ),
    ),
    (
        (
            "versionado_generico",
            r"versionado\s+(?:del|de\s+los?|de\s+las?)\s+(?:modelo|"
            r"dataset|datos|reglas?|criterios?|configuraci[oó]n)|"
            r"versi[oó]n\s+del\s+(?:modelo|dataset)",
        ),
    ),
)

GR_D09_CTRL_RECLAMOS = _crear_guardrail(
    "GR-D09-CTRL-RECLAMOS",
    "Control de reclamos e impugnaciones",
    DimensionEtica.D09,
    FamiliaGuardrail.CONTROL,
    ("D09-C7",),
    (
        "Verifica si existe un canal o procedimiento para reclamos, "
        "apelaciones o solicitudes de revision."
    ),
    (
        (
            "canal_de_reclamo",
            _coocurrencia(
                r"(?:reclamo|apelaci[oó]n|impugnaci[oó]n|solicitud\s+de\s+"
                r"revisi[oó]n)",
                r"(?:canal|formulario|correo|portal|procedimiento|plazo|"
                r"responsable)",
            ),
        ),
    ),
    (
        (
            "reclamo_sin_canal",
            r"(?:presentar|recibir|atender)\w*.{0,40}(?:reclamos?|"
            r"apelaciones?|impugnaciones?)|derecho\s+a\s+reclamo",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D09_CTRL_REPARACION = _crear_guardrail(
    "GR-D09-CTRL-REPARACION",
    "Control de correccion y reparacion",
    DimensionEtica.D09,
    FamiliaGuardrail.CONTROL,
    ("D09-C8",),
    (
        "Verifica si se preven correcciones, reparacion o seguimiento ante "
        "errores documentados."
    ),
    (
        (
            "reparacion_ante_error",
            _coocurrencia(
                r"(?:error|da[nñ]o|reclamo|decisi[oó]n\s+incorrecta|"
                r"resultado\s+incorrecto)",
                r"(?:corregir|reparar|rectificar|actualizar\s+la\s+"
                r"decisi[oó]n|notificar\s+la\s+correcci[oó]n|seguimiento)",
            ),
        ),
    ),
    (
        (
            "correccion_generica",
            r"procedimiento\s+de\s+(?:correcci[oó]n|reparaci[oó]n)|"
            r"corregir\w*.{0,45}(?:errores?|decisi[oó]n(?:es)?)",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D09_QUAL_DIFUSO = _crear_guardrail(
    "GR-D09-QUAL-DIFUSO",
    "Calidad documental de la responsabilidad",
    DimensionEtica.D09,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D09-C1", "D09-C2", "D09-C6"),
    (
        "Verifica si la responsabilidad y la auditoria se asignan a roles "
        "concretos y no quedan formuladas de manera difusa."
    ),
    (
        (
            "responsabilidad_concreta",
            r"(?:responsable\s+de\s+datos|propietario\s+del\s+modelo|"
            r"equipo\s+de\s+operaciones|comit[eé]\s+de\s+auditor[ií]a|"
            r"auditor\s+interno).{0,90}(?:deber[aá]|aprobar|revisar|"
            r"validar|auditar|responder|gestionar)\w*",
        ),
    ),
    (
        (
            "responsabilidad_difusa",
            r"(?:sistema|modelo).{0,45}(?:ser[aá]\s+auditado|tendr[aá]\s+"
            r"responsables?)|(?:se\s+realizar[aá]n?|se\s+efectuar[aá]n?)"
            r".{0,35}auditor[ií]as?|responsabilidad\s+compartida",
        ),
    ),
)

GUARDRAILS_D09: Tuple[GuardrailLexico, ...] = (
    GR_D09_PRES_RESPONSABLES,
    GR_D09_RESP_ROLES,
    GR_D09_VERIF_REGISTROS,
    GR_D09_VERIF_VERSIONADO,
    GR_D09_CTRL_RECLAMOS,
    GR_D09_CTRL_REPARACION,
    GR_D09_QUAL_DIFUSO,
)


# D10 - Impacto social y ambiental
GR_D10_PRES_IMPACTO = _crear_guardrail(
    "GR-D10-PRES-IMPACTO",
    "Presencia de impactos sociales, laborales o ambientales",
    DimensionEtica.D10,
    FamiliaGuardrail.PRESENCIA,
    ("D10-C1", "D10-C4", "D10-C6"),
    (
        "Verifica si la ERS considera impactos que exceden el desempeno "
        "tecnico inmediato."
    ),
    (
        (
            "impacto_delimitado",
            _coocurrencia(
                r"(?:impacto\s+social|impacto\s+laboral|impacto\s+"
                r"ambiental|efecto\s+sobre|consecuencia\s+sobre)",
                r"(?:personas?|comunidades?|trabajadores?|empleados?|"
                r"terceros?|grupos?|consumo\s+energ[eé]tico|emisiones?)",
            ),
        ),
    ),
    (
        (
            "impacto_generico",
            r"impacto\s+(?:social|laboral|organizacional|ambiental)|"
            r"(?:sistema|modelo).{0,50}(?:inclusivo|sostenible)",
        ),
    ),
)

GR_D10_DELIM_AFECTADOS = _crear_guardrail(
    "GR-D10-DELIM-AFECTADOS",
    "Delimitacion de personas y grupos afectados",
    DimensionEtica.D10,
    FamiliaGuardrail.DELIMITACION,
    ("D10-C1", "D10-C3", "D10-C4", "D10-C6"),
    (
        "Verifica si se identifican personas, grupos o terceros afectados "
        "por impactos amplios."
    ),
    (
        (
            "afectados_identificados",
            _coocurrencia(
                r"(?:personas?|comunidades?|trabajadores?|empleados?|"
                r"terceros?|grupos?\s+vulnerables?|no\s+usuarios?)",
                r"(?:afectad[oa]s?|impacto|exclusi[oó]n|desventaja|carga\s+de\s+"
                r"trabajo|p[eé]rdida\s+de\s+autonom[ií]a)",
            ),
        ),
    ),
    (
        (
            "afectados_genericos",
            r"(?:personas?|grupos?|terceros?)\s+afectad[oa]s?|"
            r"impacto\s+sobre\s+(?:usuarios?|personas?|trabajadores?)",
        ),
    ),
)

GR_D10_VERIF_ACCESIBILIDAD = _crear_guardrail(
    "GR-D10-VERIF-ACCESIBILIDAD",
    "Verificabilidad de accesibilidad e inclusion",
    DimensionEtica.D10,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D10-C2", "D10-C3"),
    (
        "Verifica si se documentan criterios concretos de accesibilidad o "
        "inclusion."
    ),
    (
        (
            "accesibilidad_verificable",
            r"criterios?\s+de\s+accesibilidad.{0,60}(?:usuarios?|"
            r"operadores?|personas?|wcag)|wcag\s*\d(?:[.,]\d)?|"
            r"(?:lector\s+de\s+pantalla|navegaci[oó]n\s+por\s+teclado|"
            r"subt[ií]tulos?|contraste\s+m[ií]nimo|texto\s+alternativo)",
        ),
    ),
    (
        (
            "accesibilidad_declarativa",
            r"(?:sistema|interfaz|servicio).{0,45}(?:accesible|inclusiv[oa])|"
            r"accesibilidad\s+e\s+inclusi[oó]n",
        ),
    ),
)

GR_D10_CTRL_AUTONOMIA = _crear_guardrail(
    "GR-D10-CTRL-AUTONOMIA",
    "Control frente a manipulacion y perdida de autonomia",
    DimensionEtica.D10,
    FamiliaGuardrail.CONTROL,
    ("D10-C5",),
    (
        "Verifica si se preven controles frente a manipulacion, dependencia "
        "o perdida de autonomia."
    ),
    (
        (
            "control_de_autonomia",
            _coocurrencia(
                r"(?:usuario|persona|afectad[oa])",
                r"(?:desactivar|rechazar|modificar|configurar|salir\s+de|"
                r"optar\s+por\s+no).{0,70}(?:recomendaci[oó]n(?:es)?|"
                r"personalizaci[oó]n|decisi[oó]n\s+automatizada)|"
                r"(?:prevenir|evitar|limitar)\w*.{0,55}(?:manipulaci[oó]n|"
                r"dependencia|presi[oó]n\s+indebida)|"
                r"(?:indicar\w*|indiqu\w*|marcar\w*).{0,35}"
                r"(?:no\s+le\s+interesa|"
                r"no\s+desea).{0,45}recomendaci[oó]n",
            ),
        ),
    ),
    (
        (
            "autonomia_generica",
            r"(?:autonom[ií]a|manipulaci[oó]n|dependencia\s+excesiva|"
            r"presi[oó]n\s+indebida).{0,50}(?:usuarios?|personas?|sistema)",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D10_VERIF_SOSTENIBILIDAD = _crear_guardrail(
    "GR-D10-VERIF-SOSTENIBILIDAD",
    "Verificabilidad de consumo y sostenibilidad",
    DimensionEtica.D10,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D10-C7", "D10-C8"),
    (
        "Verifica si se consideran consumo computacional, energia o "
        "eficiencia mediante condiciones revisables."
    ),
    (
        (
            "consumo_revisable",
            _coocurrencia(
                r"(?:consumo\s+computacional|consumo\s+energ[eé]tico|"
                r"energ[ií]a|recursos?\s+computacionales?|emisiones?)",
                r"(?:medir|monitorear|revisar|reducir|optimizar)\w*.{0,70}"
                r"(?:mensual|trimestral|semestral|anual|cada\s+\d+|kwh|"
                r"umbral|inferencias?\s+masivas?)",
            ),
        ),
    ),
    (
        (
            "sostenibilidad_generica",
            r"(?:sistema|modelo).{0,45}(?:sostenible|eficiente\s+"
            r"energ[eé]ticamente)|(?:consumo|uso).{0,35}"
            r"(?:computacional|energ[eé]tico|de\s+recursos)",
        ),
    ),
)

GR_D10_CTRL_MITIGACION = _crear_guardrail(
    "GR-D10-CTRL-MITIGACION",
    "Control y revision de impactos",
    DimensionEtica.D10,
    FamiliaGuardrail.CONTROL,
    ("D10-C9", "D10-C10"),
    (
        "Verifica si se documentan medidas de mitigacion y revision de "
        "impactos identificados."
    ),
    (
        (
            "mitigacion_definida",
            _coocurrencia(
                r"(?:impacto\s+social|impacto\s+laboral|impacto\s+"
                r"ambiental|exclusi[oó]n|consumo\s+energ[eé]tico|"
                r"p[eé]rdida\s+de\s+autonom[ií]a)",
                r"(?:mitigar|reducir|compensar|corregir|revisar)\w*.{0,70}"
                r"(?:responsable|mensual|trimestral|semestral|anual|"
                r"medida|acci[oó]n|seguimiento)",
            ),
        ),
    ),
    (
        (
            "mitigacion_generica",
            r"(?:medidas?|plan).{0,35}(?:mitigaci[oó]n|reducci[oó]n)"
            r".{0,45}(?:impactos?|riesgos?)|revisi[oó]n\s+de\s+impactos?",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D10_QUAL_GENERICO = _crear_guardrail(
    "GR-D10-QUAL-GENERICO",
    "Calidad documental de impactos",
    DimensionEtica.D10,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D10-C1", "D10-C2", "D10-C7", "D10-C9"),
    (
        "Verifica si los impactos se formulan con destinatarios, criterios "
        "o medidas y no como valores abstractos."
    ),
    (
        (
            "impacto_verificable",
            _coocurrencia(
                r"(?:impacto\s+social|impacto\s+laboral|impacto\s+"
                r"ambiental|accesibilidad|sostenibilidad)",
                r"(?:personas?|grupos?|terceros?|criterios?|m[eé]tricas?|"
                r"consumo|medidas?\s+de\s+mitigaci[oó]n|responsable|"
                r"frecuencia)",
            ),
        ),
    ),
    (
        (
            "impacto_abstracto",
            r"(?:sistema|modelo|servicio).{0,45}(?:inclusivo|sostenible|"
            r"socialmente\s+responsable)|impacto\s+positivo\s+en\s+la\s+"
            r"sociedad",
        ),
    ),
)

GUARDRAILS_D10: Tuple[GuardrailLexico, ...] = (
    GR_D10_PRES_IMPACTO,
    GR_D10_DELIM_AFECTADOS,
    GR_D10_VERIF_ACCESIBILIDAD,
    GR_D10_CTRL_AUTONOMIA,
    GR_D10_VERIF_SOSTENIBILIDAD,
    GR_D10_CTRL_MITIGACION,
    GR_D10_QUAL_GENERICO,
)


GUARDRAILS_D08_D10: Tuple[GuardrailLexico, ...] = (
    GUARDRAILS_D08 + GUARDRAILS_D09 + GUARDRAILS_D10
)
