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


_CONTEXTO_TRANSPARENCIA = (
    r"(?:\bia\b|inteligencia\s+artificial|automatiz\w*|"
    r"decisi[oó]n\w*\s+automatiz\w*|transparenc\w*)"
)


def _con_contexto_transparencia(expresion: str) -> str:
    return (
        rf"(?=^.{{0,500}}{_CONTEXTO_TRANSPARENCIA})"
        rf"^.{{0,500}}(?:{expresion})"
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


# D05 - Transparencia
GR_D05_PRES_IA = _crear_guardrail(
    "GR-D05-PRES-IA",
    "Presencia de comunicacion sobre uso de IA",
    DimensionEtica.D05,
    FamiliaGuardrail.PRESENCIA,
    ("D05-C1", "D05-C8"),
    "Verifica si la ERS indica que debe comunicarse el uso de IA o automatizacion.",
    (
        (
            "uso_ia_comunicado",
            r"(?:informar|comunicar|notificar)\w*.{0,80}"
            r"(?:uso\s+de\s+(?:ia|inteligencia\s+artificial)|"
            r"(?:usa|utiliza)\s+(?:ia|inteligencia\s+artificial)|"
            r"automatizaci[oó]n)",
        ),
        (
            "salida_ia_identificada",
            r"(?:salidas?|recomendaci[oó]n(?:es)?|decisi[oó]n(?:es)?|"
            r"resultados?).{0,50}"
            r"(?:generad[oa]|producid[oa])\s+(?:total\s+o\s+parcialmente\s+)?"
            r"por\s+(?:ia|inteligencia\s+artificial)",
        ),
    ),
    (
        (
            "mencion_transparencia",
            r"transparenc(?:ia|y)|transparent[ea]|"
            r"comunicaci[oó]n\s+(?:del\s+)?uso\s+de\s+(?:ia|"
            r"inteligencia\s+artificial)",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D05_DELIM_DESTINATARIOS = _crear_guardrail(
    "GR-D05-DELIM-DESTINATARIOS",
    "Delimitacion de destinatarios de la informacion",
    DimensionEtica.D05,
    FamiliaGuardrail.DELIMITACION,
    ("D05-C2",),
    "Verifica si se identifica quien recibira la informacion sobre el sistema.",
    (
        (
            "destinatarios_definidos",
            _con_contexto_transparencia(
                r"(?:informar|comunicar|notificar)\w*.{0,35}"
                r"(?:al|a\s+los?|a\s+las?)\s+(?:usuario|operador|"
                r"supervisor|responsable|analista|revisor|afectad[oa])"
            ),
        ),
        (
            "destinatarios_en_voz_pasiva",
            _con_contexto_transparencia(
                r"(?:usuarios?|operadores?|supervisores?|responsables?|"
                r"analistas?|revisores?|afectad[oa]s?).{0,35}"
                r"(?:ser[aá]n?|deber[aá]n?\s+ser|recibir[aá]n?)\s+"
                r"(?:informad[oa]s?|notificad[oa]s?|informaci[oó]n)"
            ),
        ),
    ),
    (
        (
            "mencion_destinatarios",
            _con_contexto_transparencia(
                r"(?:informaci[oó]n|comunicaci[oó]n|aviso).{0,45}"
                r"(?:usuarios?|operadores?|supervisores?|responsables?|"
                r"analistas?|revisores?|afectad[oa]s?)"
            ),
        ),
    ),
)

GR_D05_DELIM_CONTENIDO = _crear_guardrail(
    "GR-D05-DELIM-CONTENIDO",
    "Delimitacion del contenido comunicado",
    DimensionEtica.D05,
    FamiliaGuardrail.DELIMITACION,
    ("D05-C3",),
    "Verifica si se define la informacion minima que debe comunicarse.",
    (
        (
            "contenido_minimo",
            _con_contexto_transparencia(
                r"(?:informar|comunicar|notificar|mostrar|proporcionar|"
                r"recibir)\w*.{0,80}(?:finalidad|funcionamiento|"
                r"l[ií]mites?|condiciones\s+de\s+uso|uso\s+de\s+"
                r"(?:ia|inteligencia\s+artificial)|automatizaci[oó]n)"
            ),
        ),
    ),
    (
        (
            "mencion_informacion_clara",
            _con_contexto_transparencia(
                r"(?:informaci[oó]n|comunicaci[oó]n).{0,35}"
                r"(?:clara|comprensible|contenido\s+m[ií]nimo)"
            ),
        ),
    ),
)

GR_D05_VERIF_CANAL = _crear_guardrail(
    "GR-D05-VERIF-CANAL",
    "Verificabilidad del momento y canal de comunicacion",
    DimensionEtica.D05,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D05-C4",),
    "Verifica si se define cuando y por que canal se comunica la informacion.",
    (
        (
            "momento_comunicacion",
            _con_contexto_transparencia(
                r"(?:inform|comunic|notific)\w*.{0,100}"
                r"(?:antes\s+de|cuando|al\s+momento|cada\s+vez)|"
                r"(?:antes\s+de|cuando|al\s+momento|cada\s+vez).{0,100}"
                r"(?:inform|comunic|notific)\w*"
            ),
        ),
        (
            "canal_comunicacion",
            _con_contexto_transparencia(
                r"(?:informar|comunicar|notificar|aviso|informaci[oó]n)"
                r".{0,80}(?:mediante|a\s+trav[eé]s\s+de|en)\s+"
                r"(?:una?\s+)?(?:pantalla|correo|notificaci[oó]n|"
                r"interfaz|panel)|(?:pantalla|correo|notificaci[oó]n|"
                r"interfaz|panel).{0,45}(?:informaci[oó]n|aviso|"
                r"notificaci[oó]n)"
            ),
        ),
    ),
    (
        (
            "mencion_comunicacion",
            _con_contexto_transparencia(
                r"(?:comunicar|informar|notificar)\w*.{0,50}"
                r"(?:usuarios?|operadores?|uso\s+de\s+(?:ia|"
                r"inteligencia\s+artificial)|decisi[oó]n(?:es)?|"
                r"recomendaci[oó]n(?:es)?)"
            ),
        ),
    ),
)

GR_D05_VERIF_LIMITES = _crear_guardrail(
    "GR-D05-VERIF-LIMITES",
    "Verificabilidad de limites y advertencias comunicados",
    DimensionEtica.D05,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D05-C5", "D05-C6"),
    (
        "Verifica si se documentan limites, incertidumbres o advertencias "
        "que deben comunicarse."
    ),
    (
        (
            "limites_y_advertencias",
            _con_contexto_transparencia(
                r"(?:informar|comunicar|notificar|mostrar|proporcionar|"
                r"recibir|incluir|incluy|advertir)\w*.{0,90}"
                r"(?:l[ií]mites?|limitaciones?|advertencias?|incertidumbre|"
                r"errores?\s+posibles)|(?:l[ií]mites?|limitaciones?|"
                r"advertencias?|incertidumbre|errores?\s+posibles).{0,70}"
                r"(?:informar|comunicar|notificar|mostrar|advertir)\w*"
            ),
        ),
    ),
    (
        (
            "mencion_limites",
            _con_contexto_transparencia(
                r"(?:informaci[oó]n|comunicaci[oó]n|aviso).{0,60}"
                r"(?:l[ií]mites?|limitaciones?|advertencias?|incertidumbre)|"
                r"(?:l[ií]mites?|limitaciones?|advertencias?|incertidumbre)"
                r".{0,60}(?:usuarios?|operadores?|comunicaci[oó]n)"
            ),
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D05_RESP_ACTUALIZACION = _crear_guardrail(
    "GR-D05-RESP-ACTUALIZACION",
    "Responsabilidad de actualizacion de la informacion",
    DimensionEtica.D05,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D05-C10",),
    (
        "Verifica si se asigna responsable o condicion para mantener "
        "actualizada la informacion comunicada."
    ),
    (
        (
            "informacion_actualizada",
            r"(?:responsable|rol|equipo).{0,55}actualizar\w*.{0,50}"
            r"(?:informaci[oó]n\s+comunicada|informaci[oó]n\s+sobre\s+"
            r"(?:el\s+)?(?:sistema|uso\s+de\s+ia)|avisos?|advertencias?)|"
            r"actualizar\w*.{0,50}(?:informaci[oó]n\s+comunicada|avisos?|"
            r"advertencias?).{0,50}(?:cuando|ante|cada|responsable)",
        ),
    ),
    (
        (
            "mencion_actualizacion",
            r"actualizaci[oó]n\s+de\s+(?:la\s+)?(?:informaci[oó]n\s+"
            r"comunicada|avisos?|advertencias?)",
        ),
    ),
)

GR_D05_QUAL_DECLARATIVO = _crear_guardrail(
    "GR-D05-QUAL-DECLARATIVO",
    "Calidad documental de la transparencia",
    DimensionEtica.D05,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D05-C3", "D05-C5", "D05-C6"),
    (
        "Verifica si la transparencia aparece como evidencia verificable "
        "y no solo como declaracion general."
    ),
    (
        (
            "transparencia_verificable",
            r"transparencia\s+(?:verificable|documentada)|"
            r"informaci[oó]n\s+m[ií]nima.{0,45}"
            r"(?:uso\s+de\s+(?:ia|inteligencia\s+artificial)|"
            r"decisi[oó]n(?:es)?\s+automatizadas?)",
        ),
    ),
    (
        (
            "transparencia_declarativa",
            r"(?:sistema|uso\s+de\s+(?:ia|inteligencia\s+artificial))"
            r".{0,35}transparente|comunicaci[oó]n\s+adecuada.{0,35}"
            r"(?:usuarios?|uso\s+de\s+(?:ia|inteligencia\s+artificial))",
        ),
    ),
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
    (
        "Verifica si la ERS contempla explicaciones o justificaciones de "
        "salidas relevantes."
    ),
    (
        (
            "explicacion_de_salida",
            r"(?:explicaci[oó]n|justificaci[oó]n)\s+(?:asociada\s+)?"
            r"(?:a|de)\s+(?:la|las|el|los)?\s*(?:recomendaci[oó]n(?:es)?|"
            r"decisi[oó]n(?:es)?|salidas?|resultados?)|"
            r"(?:recomendaci[oó]n(?:es)?|decisi[oó]n(?:es)?|salidas?|"
            r"resultados?).{0,120}(?:incluir|proporcionar|generar|registrar)"
            r"\w*.{0,50}(?:explicaci[oó]n|justificaci[oó]n)|"
            r"(?:informar|proporcionar|mostrar)\w*.{0,80}"
            r"(?:explicaci[oó]n|factores?\s+principales|razones?\s+"
            r"principales)",
        ),
    ),
    (
        (
            "mencion_explicabilidad",
            r"(?:sistema|modelo|decisi[oó]n(?:es)?|"
            r"recomendaci[oó]n(?:es)?|salidas?)"
            r".{0,45}(?:explicab(?:le|ilidad)|interpretabilidad)|"
            r"explicaciones?\s+adecuadas?",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D06_DELIM_SALIDAS = _crear_guardrail(
    "GR-D06-DELIM-SALIDAS",
    "Delimitacion de salidas que requieren explicacion",
    DimensionEtica.D06,
    FamiliaGuardrail.DELIMITACION,
    ("D06-C1",),
    "Verifica si se identifican las salidas que requieren explicacion.",
    (
        (
            "salidas_identificadas",
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?).{0,100}"
            r"(?:deber[aá]n?|requieren?|ser[aá]n?)\s+(?:ser\s+)?"
            r"(?:explicad|justificad)\w*|"
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,80}"
            r"(?:de|para).{0,20}(?:decisi[oó]n(?:es)?|"
            r"recomendaci[oó]n(?:es)?|salidas?|resultados?)|"
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?).{0,180}(?:informar|proporcionar|mostrar)\w*"
            r".{0,80}(?:explicaci[oó]n|factores?\s+principales|"
            r"razones?\s+principales)",
        ),
    ),
    (
        (
            "mencion_salida_explicable",
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?).{0,80}"
            r"(?:explicab|explicaci[oó]n|justificaci[oó]n|interpretaci[oó]n)",
        ),
    ),
)

GR_D06_DELIM_DESTINATARIOS = _crear_guardrail(
    "GR-D06-DELIM-DESTINATARIOS",
    "Delimitacion de destinatarios de explicaciones",
    DimensionEtica.D06,
    FamiliaGuardrail.DELIMITACION,
    ("D06-C2",),
    "Verifica si se identifican los destinatarios de las explicaciones.",
    (
        (
            "destinatario_explicacion",
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,45}"
            r"(?:para|al|a\s+los?|a\s+las?)\s+(?:usuario|operador|"
            r"supervisor|revisor|afectad[oa]|analista)|"
            r"(?:informar|proporcionar|mostrar)\w*.{0,40}"
            r"(?:al|a\s+los?|a\s+las?)\s+(?:usuario|operador|supervisor|"
            r"revisor|afectad[oa]|analista).{0,80}(?:explicaci[oó]n|"
            r"factores?|razones?|criterios?)",
        ),
    ),
    (
        (
            "mencion_receptor_explicacion",
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,70}"
            r"(?:usuarios?|operadores?|supervisores?|revisores?|"
            r"afectad[oa]s?|analistas?)|(?:usuarios?|operadores?|"
            r"supervisores?|revisores?|afectad[oa]s?|analistas?).{0,70}"
            r"(?:explicaci[oó]n|justificaci[oó]n)",
        ),
    ),
)

GR_D06_VERIF_FORMATO = _crear_guardrail(
    "GR-D06-VERIF-FORMATO",
    "Verificabilidad del formato y detalle de la explicacion",
    DimensionEtica.D06,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D06-C4", "D06-C5", "D06-C6", "D06-C7"),
    (
        "Verifica si se define el formato, contenido, nivel de detalle o "
        "factores de la explicacion."
    ),
    (
        (
            "formato_explicacion",
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,90}"
            r"(?:factores?|razones?|criterios?)\s+(?:principales|"
            r"considerados)|(?:factores?|razones?|criterios?)\s+"
            r"(?:principales|considerados).{0,90}(?:explicaci[oó]n|"
            r"informar|proporcionar)|nivel\s+de\s+detalle.{0,60}"
            r"(?:explicaci[oó]n|justificaci[oó]n)|formato\s+(?:de\s+)?"
            r"(?:texto|visual|gr[aá]fico).{0,60}(?:explicaci[oó]n|"
            r"justificaci[oó]n)",
        ),
    ),
    (
        (
            "mencion_formato_explicacion",
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,60}"
            r"(?:factores?|razones?|criterios?|formato|detalle)|"
            r"(?:factores?|razones?|criterios?|formato|detalle).{0,60}"
            r"(?:explicaci[oó]n|justificaci[oó]n)",
        ),
    ),
)

GR_D06_VERIF_UTILIDAD = _crear_guardrail(
    "GR-D06-VERIF-UTILIDAD",
    "Verificabilidad de la utilidad de la explicacion",
    DimensionEtica.D06,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D06-C10",),
    (
        "Verifica si se indica como se revisara que la explicacion sea "
        "util para su destinatario."
    ),
    (
        (
            "utilidad_revisada",
            r"(?:revisar|validar|evaluar)\w*.{0,40}(?:utilidad|"
            r"suficiencia).{0,50}(?:explicaci[oó]n|justificaci[oó]n)|"
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,40}"
            r"(?:[uú]til|comprensible|suficiente).{0,60}"
            r"(?:usuario|operador|analista|revisor|afectad[oa])",
        ),
    ),
    (
        (
            "mencion_utilidad",
            r"(?:utilidad|suficiencia|adecuaci[oó]n).{0,50}"
            r"(?:explicaci[oó]n|justificaci[oó]n)|(?:explicaci[oó]n|"
            r"justificaci[oó]n).{0,50}(?:[uú]til|suficiente|adecuada)",
        ),
    ),
)

GR_D06_CTRL_REVISION = _crear_guardrail(
    "GR-D06-CTRL-REVISION",
    "Control de uso de explicaciones para revision",
    DimensionEtica.D06,
    FamiliaGuardrail.CONTROL,
    ("D06-C9",),
    (
        "Verifica si la explicacion puede usarse para revision, reclamo o "
        "analisis posterior."
    ),
    (
        (
            "explicacion_para_revision",
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,100}"
            r"(?:revisi[oó]n|reclamo|apelaci[oó]n|an[aá]lisis\s+posterior)|"
            r"(?:usar|utilizar)\w*.{0,30}(?:explicaci[oó]n|"
            r"justificaci[oó]n).{0,40}(?:revisi[oó]n|reclamo|"
            r"apelaci[oó]n|an[aá]lisis)",
        ),
    ),
    (
        (
            "mencion_revision_explicacion",
            r"(?:revisi[oó]n|reclamo|apelaci[oó]n|an[aá]lisis\s+posterior)"
            r".{0,80}(?:explicaci[oó]n|justificaci[oó]n)|"
            r"(?:explicaci[oó]n|justificaci[oó]n).{0,80}"
            r"(?:revisi[oó]n|reclamo|apelaci[oó]n|an[aá]lisis\s+posterior)",
        ),
    ),
)

GR_D06_RESP_EXPLICACION = _crear_guardrail(
    "GR-D06-RESP-EXPLICACION",
    "Responsabilidad sobre las explicaciones",
    DimensionEtica.D06,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D06-C10",),
    "Verifica si se asigna responsable de revisar o validar explicaciones.",
    (
        (
            "responsable_explicaciones",
            r"(?:responsable|rol|equipo|analista|revisor).{0,55}"
            r"(?:revisar|validar|evaluar)\w*.{0,50}(?:utilidad|"
            r"explicaci[oó]n|justificaci[oó]n)",
        ),
    ),
    (
        (
            "mencion_responsable_explicacion",
            r"(?:responsable|rol|equipo).{0,60}(?:explicaci[oó]n|"
            r"justificaci[oó]n)|(?:explicaci[oó]n|justificaci[oó]n)"
            r".{0,60}(?:responsable|rol|equipo)",
        ),
    ),
)

GR_D06_QUAL_DECLARATIVO = _crear_guardrail(
    "GR-D06-QUAL-DECLARATIVO",
    "Calidad documental de la explicabilidad",
    DimensionEtica.D06,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D06-C4", "D06-C8"),
    (
        "Verifica si la explicabilidad aparece como evidencia verificable "
        "y no solo como aspiracion."
    ),
    (
        (
            "explicabilidad_verificable",
            r"explicaci[oó]n\w*.{0,35}(?:definida|documentada|"
            r"verificable)|criterios?\s+de\s+explicabilidad|"
            r"(?:explicaci[oó]n|interpretabilidad).{0,55}"
            r"(?:limitada|limitaciones?|incertidumbre)",
        ),
    ),
    (
        (
            "explicabilidad_declarativa",
            r"(?:sistema|modelo|decisi[oó]n(?:es)?|"
            r"recomendaci[oó]n(?:es)?).{0,45}"
            r"explicable|explicaciones?\s+adecuadas?",
        ),
    ),
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
    (
        (
            "supervision_humana",
            r"supervisi[oó]n\s+humana|intervenci[oó]n\s+humana|"
            r"supervisor\w*\s+autorizad[oa]",
        ),
    ),
    (
        (
            "mencion_revision_humana",
            r"revisi[oó]n\s+humana|personal\s+autorizado.{0,45}"
            r"(?:revisar|intervenir|supervisar)|(?:decisi[oó]n(?:es)?|"
            r"recomendaci[oó]n(?:es)?|salidas?).{0,60}revisad[oa]s?.{0,45}"
            r"personal\s+autorizado",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D07_DELIM_DECISIONES = _crear_guardrail(
    "GR-D07-DELIM-DECISIONES",
    "Delimitacion de decisiones supervisadas",
    DimensionEtica.D07,
    FamiliaGuardrail.DELIMITACION,
    ("D07-C1",),
    "Verifica si se identifican decisiones o salidas sujetas a supervision.",
    (
        (
            "decisiones_supervisadas",
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?).{0,100}"
            r"(?:deber[aá]n?|ser[aá]n?|requieren?)\s+(?:ser\s+)?"
            r"(?:revisad|supervisad)\w*|(?:revisar|supervisar)\w*.{0,80}"
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?)",
        ),
    ),
    (
        (
            "mencion_decisiones_supervisadas",
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?).{0,80}"
            r"(?:revisi[oó]n|supervisi[oó]n|intervenci[oó]n)|"
            r"(?:revisi[oó]n|supervisi[oó]n|intervenci[oó]n).{0,80}"
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?)",
        ),
    ),
)

GR_D07_DELIM_ROLES = _crear_guardrail(
    "GR-D07-DELIM-ROLES",
    "Delimitacion de roles de supervision",
    DimensionEtica.D07,
    FamiliaGuardrail.DELIMITACION,
    ("D07-C2",),
    "Verifica si se identifican responsables humanos de revisar o intervenir.",
    (
        (
            "rol_supervisor",
            r"supervisor\w*\s+(?:autorizad[oa]|responsable)|"
            r"personal\s+autorizado.{0,50}(?:revisar|intervenir|supervisar)|"
            r"(?:responsable|rol|equipo).{0,50}(?:revisi[oó]n\s+humana|"
            r"supervisi[oó]n|intervenci[oó]n)",
        ),
    ),
    (
        (
            "mencion_rol_supervision",
            r"(?:supervisor\w*|personal\s+autorizado|responsable\w*)"
            r".{0,60}(?:revisar|intervenir|supervisar|revisi[oó]n|"
            r"supervisi[oó]n)|(?:revisi[oó]n|supervisi[oó]n|intervenci[oó]n)"
            r".{0,60}(?:supervisor\w*|personal\s+autorizado|responsable\w*)",
        ),
    ),
)

GR_D07_CTRL_INTERVENCION = _crear_guardrail(
    "GR-D07-CTRL-INTERVENCION",
    "Control de autoridad de intervencion",
    DimensionEtica.D07,
    FamiliaGuardrail.CONTROL,
    ("D07-C3",),
    (
        "Verifica si existe capacidad documentada de aprobar, rechazar, "
        "corregir, pausar o escalar resultados."
    ),
    (
        (
            "autoridad_intervencion",
            r"(?:supervisor|revisor|persona|personal|humano|responsable)"
            r".{0,100}(?:aprobar|rechazar|corregir|pausar|detener|escalar)"
            r"\w*.{0,35}(?:aprobar|rechazar|corregir|pausar|detener|"
            r"escalar)\w*",
        ),
    ),
    (
        (
            "mencion_intervencion",
            r"(?:supervisor|revisor|persona|personal|humano|responsable)"
            r".{0,80}(?:aprobar|rechazar|corregir|pausar|detener|escalar)"
            r"\w*|(?:aprobar|rechazar|corregir|pausar|detener|escalar)"
            r"\w*.{0,80}(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|"
            r"salidas?|resultados?)",
        ),
    ),
    PrioridadDocumental.ALTA,
)

GR_D07_VERIF_ACTIVACION = _crear_guardrail(
    "GR-D07-VERIF-ACTIVACION",
    "Verificabilidad de condiciones de activacion",
    DimensionEtica.D07,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D07-C4",),
    "Verifica si se definen las condiciones que activan la revision humana.",
    (
        (
            "condicion_revision",
            r"(?:si|cuando|ante|en\s+caso\s+de).{0,45}"
            r"(?:diferencia|incertidumbre|alto\s+riesgo|riesgo|conflicto|"
            r"excepci[oó]n).{0,70}(?:revisi[oó]n|revisad\w*|supervisi[oó]n|"
            r"intervenci[oó]n)|"
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?|"
            r"resultados?).{0,70}"
            r"(?:alto\s+riesgo|incertidumbre|conflicto|excepci[oó]n)"
            r".{0,80}(?:deber[aá]|requiere|ser[aá]).{0,25}"
            r"(?:revisad|supervisad|escalad)\w*",
        ),
    ),
    (
        (
            "mencion_activacion",
            r"condici[oó]n\w*.{0,45}(?:revisi[oó]n|intervenci[oó]n|"
            r"supervisi[oó]n)|(?:alto\s+riesgo|incertidumbre|conflicto|"
            r"excepci[oó]n).{0,70}(?:revisi[oó]n|revisad\w*|supervisi[oó]n|"
            r"intervenci[oó]n)",
        ),
    ),
)

GR_D07_VERIF_PROCEDIMIENTO = _crear_guardrail(
    "GR-D07-VERIF-PROCEDIMIENTO",
    "Verificabilidad del procedimiento de revision",
    DimensionEtica.D07,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("D07-C5", "D07-C6", "D07-C10"),
    (
        "Verifica si se define un procedimiento de revision, escalamiento "
        "e informacion disponible."
    ),
    (
        (
            "procedimiento_revision",
            r"procedimiento\s+(?:documentado\s+)?de\s+(?:revisi[oó]n|"
            r"intervenci[oó]n|escalamiento)|pasos\s+(?:para|de)\s+"
            r"(?:revisar|intervenir|escalar)|(?:supervisor|revisor|personal)"
            r".{0,80}informaci[oó]n\s+disponible",
        ),
    ),
    (
        (
            "mencion_procedimiento",
            r"procedimiento.{0,40}(?:revisi[oó]n|intervenci[oó]n|"
            r"escalamiento)|pasos\s+de\s+(?:revisi[oó]n|intervenci[oó]n)|"
            r"informaci[oó]n\s+disponible.{0,45}(?:supervisor|revisor)",
        ),
    ),
)

GR_D07_RESP_REGISTRO = _crear_guardrail(
    "GR-D07-RESP-REGISTRO",
    "Responsabilidad y registro de la intervencion",
    DimensionEtica.D07,
    FamiliaGuardrail.RESPONSABILIDAD,
    ("D07-C8",),
    "Verifica si se documenta que debe registrarse de la intervencion humana.",
    (
        (
            "registro_intervencion",
            r"registr\w*.{0,35}(?:motivo|decisi[oó]n(?:es)?\s+humanas?|"
            r"intervenci[oó]n|revisi[oó]n\s+humana)|registro\s+"
            r"(?:de\s+la\s+)?(?:intervenci[oó]n|revisi[oó]n\s+humana)",
        ),
    ),
    (
        (
            "mencion_registro",
            r"(?:registrar\w*|registro\w*).{0,50}(?:intervenci[oó]n|"
            r"revisi[oó]n|supervisi[oó]n|motivo)|(?:intervenci[oó]n|"
            r"revisi[oó]n|supervisi[oó]n).{0,50}(?:registrar\w*|registro\w*)",
        ),
    ),
)

GR_D07_QUAL_DECLARATIVO = _crear_guardrail(
    "GR-D07-QUAL-DECLARATIVO",
    "Calidad documental de la supervision humana",
    DimensionEtica.D07,
    FamiliaGuardrail.CALIDAD_DOCUMENTAL,
    ("D07-C2", "D07-C3", "D07-C4", "D07-C5"),
    "Verifica si la supervision humana es verificable y no solo declarativa.",
    (
        (
            "supervision_verificable",
            r"supervisi[oó]n\s+humana\s+(?:obligatoria|definida|"
            r"documentada)|revisi[oó]n\s+humana\s+(?:obligatoria|"
            r"documentada)|(?:decisi[oó]n(?:es)?|"
            r"recomendaci[oó]n(?:es)?|salidas?)"
            r".{0,80}(?:deber[aá]n?|requieren?)\s+ser\s+revisad\w*"
            r".{0,80}supervisor\w*\s+autorizad[oa]",
        ),
    ),
    (
        (
            "supervision_declarativa",
            r"(?:decisi[oó]n(?:es)?|recomendaci[oó]n(?:es)?|salidas?)"
            r"\s+podr[aá]n\s+"
            r"ser\s+revisad[oa]s?|supervisi[oó]n\s+humana",
        ),
    ),
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

GUARDRAILS_D05_D07: Tuple[GuardrailLexico, ...] = (
    GUARDRAILS_D05 + GUARDRAILS_D06 + GUARDRAILS_D07
)
