"""Guardrails que solo aplican cuando la ERS declara un dominio concreto.

Complementan el catalogo general D01-D10 con exigencias propias de dominios
de alto riesgo. Cada guardrail se asocia a la dimension que especializa, por
lo que su resultado participa de la consolidacion y de la ponderacion de esa
dimension.
"""

from __future__ import annotations

from itertools import permutations
from typing import Tuple

from etica_ia_ers.dominio import (
    DefinicionGuardrail,
    DimensionEtica,
    DominioAplicacion,
    EstadoGuardrail,
    FamiliaGuardrail,
    PrioridadDocumental,
)

from .guardrail_lexico import GuardrailLexico, senal


def _en_mismo_enunciado(*conceptos: str, distancia: int = 120) -> str:
    """Exige todos los conceptos, en cualquier orden, sin cruzar un punto."""
    separador = rf"[^.;]{{0,{distancia}}}"
    return "|".join(
        separador.join(rf"(?:{concepto})" for concepto in orden)
        for orden in permutations(conceptos)
    )


def _crear_guardrail(
    codigo: str,
    nombre: str,
    dominio: DominioAplicacion,
    dimension: DimensionEtica,
    familia: FamiliaGuardrail,
    criterios: Tuple[str, ...],
    descripcion: str,
    explicitas: Tuple[Tuple[str, str], ...],
    parciales: Tuple[Tuple[str, str], ...],
    prioridad: PrioridadDocumental = PrioridadDocumental.ALTA,
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
            dominios=(dominio,),
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


_NEGACION_DE_USO = (
    r"(?:no\s+(?:debera|deberan|podra|podran|se\s+podra|se\s+debera)\s+"
    r"(?:utilizar|usar|considerar|emplear|incluir)|"
    r"se\s+(?:excluir\w*|prohib\w*)|excluir\w*|prohib\w*)"
)

_INFORMAR = r"(?:informar\w*|notificar\w*|comunicar\w*|avisar\w*|explicar\w*)"


# Credito y finanzas
GR_D06_VERIF_CRED_MOTIVOS = _crear_guardrail(
    "GR-D06-VERIF-CRED-MOTIVOS",
    "Explicacion de motivos al solicitante de credito",
    DominioAplicacion.CREDITICIO,
    DimensionEtica.D06,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("CRED-C1",),
    (
        "Verifica si la ERS exige comunicar al solicitante los motivos "
        "principales de un rechazo, del puntaje o de las condiciones "
        "ofrecidas."
    ),
    (
        (
            "motivos_comunicados_al_solicitante",
            _en_mismo_enunciado(
                _INFORMAR + r"|indicar\w*",
                r"solicitantes?|clientes?|personas?\s+evaluadas?",
                r"motivos?|razones?|factores?|causas?",
            ),
        ),
    ),
    (
        (
            "factores_del_puntaje_sin_destinatario",
            r"(?:motivos?|razones?|factores?|causas?|explicacion).{0,60}"
            r"(?:rechazo|denegacion|puntaje|score|decision\s+crediticia)",
        ),
    ),
)

GR_D04_DELIM_CRED_VARIABLES = _crear_guardrail(
    "GR-D04-DELIM-CRED-VARIABLES",
    "Exclusion de variables protegidas en la evaluacion crediticia",
    DominioAplicacion.CREDITICIO,
    DimensionEtica.D04,
    FamiliaGuardrail.DELIMITACION,
    ("CRED-C2",),
    (
        "Verifica si la ERS excluye atributos protegidos o sus proxies, como "
        "genero, etnia, nacionalidad o codigo postal, de la decision "
        "crediticia."
    ),
    (
        (
            "variables_protegidas_excluidas",
            _NEGACION_DE_USO
            + r"[^.;]{0,80}(?:genero|sexo|etnia|raza|origen\s+etnico|"
            r"nacionalidad|religion|estado\s+civil|edad|discapacidad|"
            r"codigo\s+postal|variables?\s+protegidas?|"
            r"atributos?\s+protegidos?)",
        ),
    ),
    (
        (
            "mencion_variables_sensibles",
            r"(?:variables?|atributos?|caracteristicas?)\s+"
            r"(?:sensibles|protegid[oa]s)|discrimina\w*",
        ),
    ),
)

GR_D09_CTRL_CRED_IMPUGNACION = _crear_guardrail(
    "GR-D09-CTRL-CRED-IMPUGNACION",
    "Impugnacion y revision de decisiones crediticias",
    DominioAplicacion.CREDITICIO,
    DimensionEtica.D09,
    FamiliaGuardrail.CONTROL,
    ("CRED-C3",),
    (
        "Verifica si el solicitante puede impugnar una decision crediticia "
        "o pedir su revision por una persona."
    ),
    (
        (
            "solicitante_puede_impugnar",
            _en_mismo_enunciado(
                r"solicitantes?|clientes?|personas?\s+evaluadas?",
                r"impugnar|apelar|recurrir|reconsideracion|"
                r"solicitar\s+(?:una\s+)?revision",
                r"decision\w*|puntajes?|rechazos?|resultados?|evaluacion\w*",
            ),
        ),
    ),
    (
        (
            "mencion_impugnacion",
            r"impugnacion\w*|apelacion\w*|reconsideracion",
        ),
    ),
)


# Salud
GR_D07_CTRL_SALUD_DECISION = _crear_guardrail(
    "GR-D07-CTRL-SALUD-DECISION",
    "Decision clinica final a cargo de un profesional de la salud",
    DominioAplicacion.SALUD,
    DimensionEtica.D07,
    FamiliaGuardrail.CONTROL,
    ("SALUD-C1",),
    (
        "Verifica si la ERS reserva la decision clinica final a un "
        "profesional de la salud que valida o confirma cada resultado."
    ),
    (
        (
            "validacion_profesional_obligatoria",
            r"no\s+(?:(?:se\s+)?(?:debera|podra)\s+)?"
            r"(?:emitir\w*|generar\w*|comunicar\w*|publicar\w*)"
            r"[^.;]{0,100}sin\s+(?:la\s+)?(?:validacion|confirmacion|revision|"
            r"aprobacion)\s+(?:previa\s+)?de\s+(?:un|una|el|la)\s+"
            r"(?:profesional|medic[oa]|especialista|clinic[oa])",
        ),
        (
            "profesional_confirma_cada_resultado",
            r"(?:profesional|medic[oa]|especialista).{0,60}"
            r"(?:revis\w*|confirm\w*|valid\w*|aprob\w*).{0,40}"
            r"(?:cada|todos?\s+los?)\s+(?:resultados?|diagnosticos?|"
            r"recomendaciones?|informes?)",
        ),
    ),
    (
        (
            "apoyo_a_la_decision_clinica",
            r"apoyo\s+(?:a\s+la\s+)?decision\s+(?:medica|clinica)",
        ),
        (
            "mencion_supervision_profesional",
            r"(?:profesional|medic[oa]|especialista)\w*.{0,40}"
            r"(?:revis|supervis)\w*",
        ),
    ),
)

GR_D08_VERIF_SALUD_VALIDACION = _crear_guardrail(
    "GR-D08-VERIF-SALUD-VALIDACION",
    "Validacion clinica del desempeno del sistema",
    DominioAplicacion.SALUD,
    DimensionEtica.D08,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("SALUD-C2",),
    (
        "Verifica si la ERS exige una validacion clinica con metricas como "
        "sensibilidad o especificidad y una poblacion de referencia."
    ),
    (
        (
            "validacion_clinica_con_metricas",
            r"(?:validacion|evaluacion|estudio|ensayo)\s+"
            r"(?:clinic[oa]|prospectiv[oa]|retrospectiv[oa]|"
            r"multicentric[oa]).{0,150}(?:sensibilidad|especificidad|"
            r"valor\s+predictivo|auc|\d+(?:[.,]\d+)?\s*%)",
        ),
        (
            "metrica_clinica_con_umbral",
            r"(?:sensibilidad|especificidad|valor\s+predictivo).{0,60}"
            r"(?:\d+(?:[.,]\d+)?\s*%|minim[oa]|igual\s+o\s+superior|"
            r"no\s+inferior)",
        ),
    ),
    (
        (
            "mencion_validacion_clinica",
            r"(?:validacion|evidencia|estudio|ensayo)\s+clinic[oa]|"
            r"validad[oa]\s+clinicamente|sensibilidad|especificidad",
        ),
    ),
)

GR_D03_DELIM_SALUD_CONSENTIMIENTO = _crear_guardrail(
    "GR-D03-DELIM-SALUD-CONSENTIMIENTO",
    "Base legal y consentimiento para datos de salud",
    DominioAplicacion.SALUD,
    DimensionEtica.D03,
    FamiliaGuardrail.DELIMITACION,
    ("SALUD-C3",),
    (
        "Verifica si la ERS define el consentimiento, la base legal o la "
        "anonimizacion aplicable a los datos de salud de los pacientes."
    ),
    (
        (
            "consentimiento_informado",
            r"consentimiento\s+(?:informado|expreso|explicito).{0,100}"
            r"(?:pacientes?|titulares?|datos|tratamiento)",
        ),
        (
            "datos_clinicos_anonimizados",
            r"(?:anonimiza\w*|seudonimiza\w*|disocia\w*).{0,80}"
            r"(?:datos|imagenes?|historias?|registros?)",
        ),
    ),
    (
        # Una cita normativa contextualiza, pero no define por si sola
        # el consentimiento ni la base concreta del tratamiento.
        (
            "normativa_de_datos_de_salud",
            r"ley\s+(?:n\W{0,2}\s*)?(?:25\.?326|26\.?529)|rgpd|"
            r"reglamento\s+general\s+de\s+proteccion\s+de\s+datos|"
            r"ley\s+organica\s+3/2018|lopdgdd|hipaa",
        ),
        (
            "proteccion_generica_de_datos_clinicos",
            r"(?:confidencialidad|privacidad|proteccion).{0,60}datos.{0,30}"
            r"(?:pacientes?|clinicos|de\s+salud|historias?)",
        ),
        ("mencion_consentimiento", r"consentimiento"),
    ),
)


# Recomendacion y contenidos
GR_D05_PRES_REC_AVISO = _crear_guardrail(
    "GR-D05-PRES-REC-AVISO",
    "Aviso de personalizacion de las recomendaciones",
    DominioAplicacion.RECOMENDACION,
    DimensionEtica.D05,
    FamiliaGuardrail.PRESENCIA,
    ("REC-C1",),
    (
        "Verifica si la ERS exige informar al usuario por que se le "
        "recomienda un contenido o que el contenido fue personalizado."
    ),
    (
        (
            "motivo_de_la_recomendacion_visible",
            r"(?:informar|indicar|explicar|comunicar|mostrar)\w*[^.;]{0,80}"
            r"(?:por\s+que|motivos?|razon|razones|criterios?)[^.;]{0,60}"
            r"(?:recomendacion\w*|recomendad[oa]s?|recomienda\w*|"
            r"personaliza\w*)",
        ),
        (
            "contenido_recomendado_identificado",
            r"(?:etiquet|identific|senal|distingu)\w*[^.;]{0,60}"
            r"(?:contenidos?|elementos?|publicaciones?)\s+"
            r"(?:recomendad|personalizad|patrocinad)\w*",
        ),
    ),
    (
        (
            "transparencia_de_recomendaciones",
            r"(?:transparencia|explicacion|explicar).{0,60}"
            r"(?:recomendacion\w*|personalizacion)",
        ),
    ),
    PrioridadDocumental.MEDIA,
)

GR_D07_CTRL_REC_PERSONALIZACION = _crear_guardrail(
    "GR-D07-CTRL-REC-PERSONALIZACION",
    "Control del usuario sobre la personalizacion",
    DominioAplicacion.RECOMENDACION,
    DimensionEtica.D07,
    FamiliaGuardrail.CONTROL,
    ("REC-C2",),
    (
        "Verifica si el usuario puede desactivar la personalizacion, elegir "
        "una alternativa no personalizada o editar su perfil de intereses."
    ),
    (
        (
            "desactivar_personalizacion",
            r"(?:desactivar|deshabilitar|apagar|rechazar|optar\s+por\s+no)"
            r"\w*[^.;]{0,60}(?:personalizacion|recomendaciones\s+"
            r"personalizadas|perfilado|perfilamiento)",
        ),
        (
            "alternativa_no_personalizada",
            r"(?:version|opcion|modo|vista|feed)[^.;]{0,30}"
            r"(?:no\s+personalizad[oa]|sin\s+personalizacion|cronologic[oa])",
        ),
        (
            "edicion_del_perfil_de_intereses",
            r"(?:ajustar|modificar|editar|configurar|borrar|eliminar)\w*"
            r"[^.;]{0,40}(?:sus\s+)?(?:preferencias|perfil|historial|"
            r"intereses)",
        ),
    ),
    (
        (
            "retroalimentacion_del_usuario",
            r"usuarios?[^.;]{0,80}(?:no\s+le\s+interesa|valorar|calificar|"
            r"indicar\s+(?:sus\s+)?preferencias|retroalimentacion|feedback)",
        ),
    ),
    PrioridadDocumental.MEDIA,
)

GR_D10_CTRL_REC_MENORES = _crear_guardrail(
    "GR-D10-CTRL-REC-MENORES",
    "Proteccion de menores y contenidos nocivos en las recomendaciones",
    DominioAplicacion.RECOMENDACION,
    DimensionEtica.D10,
    FamiliaGuardrail.CONTROL,
    ("REC-C3",),
    (
        "Verifica si la ERS restringe recomendaciones no aptas para menores "
        "o contenidos nocivos, o fija una diversidad minima de contenidos."
    ),
    (
        (
            "restriccion_de_contenidos_no_aptos",
            r"(?:no\s+(?:debera|podra|se\s+podra)\s+recomendar|"
            r"excluir\w*|filtrar\w*|bloquear\w*|restringir\w*|impedir\w*)"
            r"[^.;]{0,80}(?:menores(?:\s+de\s+edad)?|ninos|ninas|"
            r"infantil\w*|adolescentes|contenidos?\s+(?:no\s+aptos?|"
            r"nocivos?|perjudiciales?|inapropiados?|para\s+adultos))",
        ),
        (
            "diversidad_minima",
            r"(?:diversidad|variedad)[^.;]{0,60}"
            r"(?:al\s+menos|minim[oa]|\d+(?:[.,]\d+)?\s*%)",
        ),
    ),
    (
        (
            "mencion_menores_o_efectos_nocivos",
            r"menores\s+de\s+edad|perfil\s+infantil|control\s+parental|"
            r"clasificacion\s+por\s+edad|contenidos?\s+(?:nocivos?|"
            r"no\s+aptos?|inapropiados?)|burbujas?\s+de\s+filtro|"
            r"camaras?\s+de\s+eco",
        ),
    ),
)


# Empleo
GR_D05_PRES_EMP_INFORMACION = _crear_guardrail(
    "GR-D05-PRES-EMP-INFORMACION",
    "Informacion a candidatos y trabajadores sobre el uso de IA",
    DominioAplicacion.EMPLEO,
    DimensionEtica.D05,
    FamiliaGuardrail.PRESENCIA,
    ("EMP-C1",),
    (
        "Verifica si la ERS exige informar a candidatos o trabajadores que "
        "un sistema de IA participa en su evaluacion."
    ),
    (
        (
            "candidatos_informados_del_uso_de_ia",
            _en_mismo_enunciado(
                _INFORMAR,
                r"candidat\w*|postulant\w*|aspirant\w*|trabajador\w*|"
                r"emplead[oa]s?",
                r"inteligencia\s+artificial|\bia\b|algoritm\w*|"
                r"(?:sistema|evaluacion|herramienta)\s+automatizad[oa]",
            ),
        ),
    ),
    (
        (
            "transparencia_hacia_candidatos",
            r"(?:candidat|postulant|trabajador|emplead)\w*[^.;]{0,80}"
            r"(?:transparencia|informacion\s+sobre\s+el\s+proceso)",
        ),
    ),
)

GR_D04_VERIF_EMP_DISCRIMINACION = _crear_guardrail(
    "GR-D04-VERIF-EMP-DISCRIMINACION",
    "Prevencion de discriminacion en seleccion y evaluacion laboral",
    DominioAplicacion.EMPLEO,
    DimensionEtica.D04,
    FamiliaGuardrail.VERIFICABILIDAD,
    ("EMP-C2",),
    (
        "Verifica si la ERS audita el impacto dispar entre grupos de "
        "candidatos o excluye atributos protegidos de la decision laboral."
    ),
    (
        (
            "auditoria_de_impacto_dispar",
            r"(?:auditoria|evaluacion|analisis|medicion|monitoreo)\w*"
            r"[^.;]{0,40}(?:sesgos?|impacto\s+(?:dispar|adverso|"
            r"diferencial)|discriminacion)[^.;]{0,100}(?:genero|sexo|edad|"
            r"discapacidad|origen|etnia|nacionalidad|candidat\w*|"
            r"postulant\w*|seleccion)",
        ),
        (
            "atributos_protegidos_excluidos",
            _NEGACION_DE_USO
            + r"[^.;]{0,80}(?:genero|sexo|edad|embarazo|discapacidad|"
            r"estado\s+civil|origen\s+etnico|religion|"
            r"afiliacion\s+sindical)",
        ),
    ),
    (
        (
            "mencion_no_discriminacion",
            r"discrimina\w*|igualdad\s+de\s+oportunidades|sesgos?",
        ),
    ),
)

GR_D07_CTRL_EMP_DECISION = _crear_guardrail(
    "GR-D07-CTRL-EMP-DECISION",
    "Revision humana de decisiones de contratacion o desvinculacion",
    DominioAplicacion.EMPLEO,
    DimensionEtica.D07,
    FamiliaGuardrail.CONTROL,
    ("EMP-C3",),
    (
        "Verifica si una persona revisa las decisiones de seleccion, "
        "descarte, promocion o desvinculacion antes de que tengan efecto."
    ),
    (
        (
            "revision_humana_de_la_decision_laboral",
            _en_mismo_enunciado(
                r"(?:revision|validacion|aprobacion|supervision|"
                r"confirmacion|decision)\s+(?:humana|de\s+(?:un|una)\s+"
                r"(?:persona|reclutador\w*|responsable|seleccionador\w*))",
                r"contratacion|seleccion|descart\w*|rechaz\w*|despido|"
                r"desvinculacion|promocion|candidat\w*|postulant\w*",
            ),
        ),
    ),
    (
        (
            "mencion_supervision_de_rrhh",
            r"(?:reclutador\w*|responsables?\s+de\s+seleccion|"
            r"recursos\s+humanos|rrhh)[^.;]{0,80}(?:revis|supervis|valid)\w*",
        ),
    ),
)


# Educacion
GR_D03_DELIM_EDU_DATOS = _crear_guardrail(
    "GR-D03-DELIM-EDU-DATOS",
    "Tratamiento de datos de estudiantes y menores",
    DominioAplicacion.EDUCACION,
    DimensionEtica.D03,
    FamiliaGuardrail.DELIMITACION,
    ("EDU-C1",),
    (
        "Verifica si la ERS exige autorizacion de tutores o limita el uso de "
        "los datos de estudiantes a una finalidad educativa."
    ),
    (
        (
            "autorizacion_de_tutores",
            r"(?:consentimiento|autorizacion)[^.;]{0,80}(?:padres|madres|"
            r"tutores|responsables?\s+legales?|adultos?\s+responsables?)",
        ),
        (
            "datos_de_estudiantes_limitados",
            r"(?:datos|informacion)[^.;]{0,40}(?:estudiantes|alumnos|"
            r"alumnado|menores)[^.;]{0,100}(?:solo|unicamente|"
            r"exclusivamente|no\s+se\s+(?:compartiran|usaran|utilizaran)|"
            r"anonimiza\w*|seudonimiza\w*|finalidad\s+(?:educativa|"
            r"pedagogica))",
        ),
    ),
    (
        (
            "mencion_datos_de_estudiantes",
            r"(?:datos|informacion)\s+(?:personales\s+)?(?:de|del|de\s+los)"
            r"\s+(?:estudiantes|alumnos|alumnado|menores)|"
            r"privacidad\s+de\s+(?:los\s+)?(?:estudiantes|alumnos)",
        ),
    ),
)

GR_D07_CTRL_EDU_DOCENTE = _crear_guardrail(
    "GR-D07-CTRL-EDU-DOCENTE",
    "Revision docente de decisiones academicas",
    DominioAplicacion.EDUCACION,
    DimensionEtica.D07,
    FamiliaGuardrail.CONTROL,
    ("EDU-C2",),
    (
        "Verifica si un docente revisa o decide sobre calificaciones, "
        "admisiones, sanciones u otras decisiones academicas del sistema."
    ),
    (
        (
            "docente_decide_sobre_resultado_academico",
            _en_mismo_enunciado(
                r"docentes?|profesor\w*|tutor\w*\s+academic[oa]s?|"
                r"equipo\s+docente|personal\s+docente",
                r"revis\w*|valid\w*|confirm\w*|aprob\w*|decid\w*|"
                r"supervis\w*",
                r"calificacion\w*|notas?|evaluacion\w*|promocion|admision\w*|"
                r"sancion\w*|plagio",
            ),
        ),
    ),
    (
        (
            "docente_accede_a_resultados",
            r"(?:docentes?|profesor\w*)[^.;]{0,80}(?:acceder|consultar|"
            r"visualizar|recibir)\w*[^.;]{0,40}(?:resultados|alertas|"
            r"informes|reportes)",
        ),
    ),
)

GR_D04_DELIM_EDU_EQUIDAD = _crear_guardrail(
    "GR-D04-DELIM-EDU-EQUIDAD",
    "Equidad entre estudiantes de contextos diversos",
    DominioAplicacion.EDUCACION,
    DimensionEtica.D04,
    FamiliaGuardrail.DELIMITACION,
    ("EDU-C3",),
    (
        "Verifica si la ERS identifica grupos de estudiantes en desventaja "
        "y exige medir o corregir diferencias de desempeno entre ellos."
    ),
    (
        (
            "grupos_de_estudiantes_con_medicion",
            _en_mismo_enunciado(
                r"estudiantes|alumnos|alumnado",
                r"discapacidad|necesidades\s+educativas|socioeconomic\w*|"
                r"rural\w*|lengua\s+materna|neurodivergen\w*|vulnerab\w*",
                r"sesgos?|equidad|desempeno|precision|metric\w*|"
                r"compar\w*|medi\w*|ajust\w*",
                distancia=150,
            ),
        ),
    ),
    (
        (
            "mencion_equidad_educativa",
            r"inclusion\s+educativa|equidad\s+educativa|"
            r"igualdad\s+de\s+oportunidades|necesidades\s+educativas",
        ),
    ),
    PrioridadDocumental.MEDIA,
)


# Sector publico
GR_D05_PRES_PUB_TRANSPARENCIA = _crear_guardrail(
    "GR-D05-PRES-PUB-TRANSPARENCIA",
    "Transparencia algoritmica hacia la ciudadania",
    DominioAplicacion.SECTOR_PUBLICO,
    DimensionEtica.D05,
    FamiliaGuardrail.PRESENCIA,
    ("PUB-C1",),
    (
        "Verifica si la ERS exige publicar el sistema en un registro de "
        "algoritmos o informar a la ciudadania sobre su uso."
    ),
    (
        (
            "registro_publico_de_algoritmos",
            r"(?:registro|inventario|catalogo)\s+(?:publico\s+)?(?:de\s+)?"
            r"(?:algoritmos|sistemas\s+de\s+(?:ia|inteligencia\s+artificial)"
            r"|algoritmico)",
        ),
        (
            "publicacion_del_funcionamiento",
            r"(?:publicar|publicacion|difundir|portal\s+de\s+transparencia)"
            r"\w*[^.;]{0,100}(?:algoritmo|sistema\s+de\s+(?:ia|"
            r"inteligencia\s+artificial)|logica|criterios\s+de\s+decision|"
            r"codigo\s+fuente)",
        ),
        (
            "ciudadania_informada_del_uso_de_ia",
            _en_mismo_enunciado(
                _INFORMAR,
                r"ciudadan\w*|administrad[oa]s|interesad[oa]s|"
                r"personas\s+usuarias",
                r"inteligencia\s+artificial|\bia\b|algoritm\w*|"
                r"actuacion\s+administrativa\s+automatizada|"
                r"sistema\s+automatizado",
            ),
        ),
    ),
    (
        (
            "mencion_transparencia_publica",
            r"transparencia[^.;]{0,60}(?:algoritm\w*|administracion|"
            r"sector\s+publico|ciudadan\w*)",
        ),
    ),
)

GR_D09_CTRL_PUB_RECURSO = _crear_guardrail(
    "GR-D09-CTRL-PUB-RECURSO",
    "Vias de recurso ante actuaciones administrativas automatizadas",
    DominioAplicacion.SECTOR_PUBLICO,
    DimensionEtica.D09,
    FamiliaGuardrail.CONTROL,
    ("PUB-C2",),
    (
        "Verifica si la ciudadania puede recurrir o pedir la revision de "
        "una resolucion o actuacion en la que intervino el sistema."
    ),
    (
        (
            "ciudadania_puede_recurrir",
            _en_mismo_enunciado(
                r"recurso\w*|recurrir|impugnar|impugnacion|reclamacion\w*|"
                r"solicitar\s+(?:la\s+)?revision",
                r"ciudadan\w*|administrad[oa]s?|interesad[oa]s?|"
                r"personas?\s+afectadas?",
                r"resolucion\w*|actuacion\w*|decision\w*|"
                r"actos?\s+administrativos?|resultados?",
            ),
        ),
    ),
    (
        (
            "mencion_vias_de_reclamo",
            r"recursos?\s+administrativos?|vias?\s+de\s+reclamacion|"
            r"defensor\s+del\s+pueblo|atencion\s+(?:a\s+la\s+)?ciudadan\w*",
        ),
    ),
)

GR_D10_CTRL_PUB_CANAL = _crear_guardrail(
    "GR-D10-CTRL-PUB-CANAL",
    "Canal alternativo no automatizado y brecha digital",
    DominioAplicacion.SECTOR_PUBLICO,
    DimensionEtica.D10,
    FamiliaGuardrail.CONTROL,
    ("PUB-C3",),
    (
        "Verifica si la ERS mantiene un canal de atencion humano o "
        "presencial y mitiga la brecha digital de quienes no usan el sistema."
    ),
    (
        (
            "canal_alternativo_humano",
            r"(?:canal|via|atencion|alternativa|opcion)\w*\s+"
            r"(?:\w+\s+){0,3}(?:presencial|telefonic\w*|humana|"
            r"no\s+automatizad\w*|asistida)",
        ),
        (
            "brecha_digital_mitigada",
            _en_mismo_enunciado(
                r"brecha\s+digital",
                r"mitig\w*|reduc\w*|garantiz\w*|alternativ\w*|asist\w*",
            ),
        ),
    ),
    (
        (
            "mencion_inclusion_digital",
            r"brecha\s+digital|inclusion\s+digital|alfabetizacion\s+digital|"
            r"personas\s+mayores",
        ),
    ),
    PrioridadDocumental.MEDIA,
)


GUARDRAILS_CREDITICIO: Tuple[GuardrailLexico, ...] = (
    GR_D04_DELIM_CRED_VARIABLES,
    GR_D06_VERIF_CRED_MOTIVOS,
    GR_D09_CTRL_CRED_IMPUGNACION,
)

GUARDRAILS_SALUD: Tuple[GuardrailLexico, ...] = (
    GR_D03_DELIM_SALUD_CONSENTIMIENTO,
    GR_D07_CTRL_SALUD_DECISION,
    GR_D08_VERIF_SALUD_VALIDACION,
)

GUARDRAILS_RECOMENDACION: Tuple[GuardrailLexico, ...] = (
    GR_D05_PRES_REC_AVISO,
    GR_D07_CTRL_REC_PERSONALIZACION,
    GR_D10_CTRL_REC_MENORES,
)

GUARDRAILS_EMPLEO: Tuple[GuardrailLexico, ...] = (
    GR_D04_VERIF_EMP_DISCRIMINACION,
    GR_D05_PRES_EMP_INFORMACION,
    GR_D07_CTRL_EMP_DECISION,
)

GUARDRAILS_EDUCACION: Tuple[GuardrailLexico, ...] = (
    GR_D03_DELIM_EDU_DATOS,
    GR_D04_DELIM_EDU_EQUIDAD,
    GR_D07_CTRL_EDU_DOCENTE,
)

GUARDRAILS_SECTOR_PUBLICO: Tuple[GuardrailLexico, ...] = (
    GR_D05_PRES_PUB_TRANSPARENCIA,
    GR_D09_CTRL_PUB_RECURSO,
    GR_D10_CTRL_PUB_CANAL,
)

GUARDRAILS_POR_DOMINIO: Tuple[GuardrailLexico, ...] = (
    GUARDRAILS_CREDITICIO
    + GUARDRAILS_SALUD
    + GUARDRAILS_RECOMENDACION
    + GUARDRAILS_EMPLEO
    + GUARDRAILS_EDUCACION
    + GUARDRAILS_SECTOR_PUBLICO
)
