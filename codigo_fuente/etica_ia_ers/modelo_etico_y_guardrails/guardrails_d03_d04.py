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
            r"datos\s+(?:de\s+entrenamiento|de\s+validacion|de\s+inferencia|"
            r"sensibles|biometricos|clinicos|de\s+salud|financieros|"
            r"crediticios|demograficos|de\s+ubicacion|de\s+identificacion|"
            r"personales(?!\s+y\s+(?:a\s+la\s+libre\s+circulaci[oó]n|"
            r"garantia))\b)",
        ),
        senal(
            "origen_de_datos_especifico",
            r"(?:proceden|proceder|procederan|provienen|provenir|provendran|"
            r"obtenerse|recopilarse|se\s+obtienen|"
            r"se\s+obtendran|se\s+recopilan|se\s+recopilaran)\s+de\s+"
            r"(?:registros|fuentes|bases\s+de\s+datos|formularios|sensores|"
            r"historias\s+clinicas)(?:\s+(?:autorizad[oa]s|oficiales|"
            r"internas|institucionales))?",
        ),
        senal(
            "datos_provistos_por_fuente_autorizada",
            r"datos.{0,45}provistos?\s+por\s+(?:entidades|fuentes|"
            r"instituciones)\s+autorizadas?",
        ),
        senal(
            "datos_clinicos_del_paciente",
            r"(?:datos\s+(?:del|de\s+los)\s+pacientes?|"
            r"imagenes?\s+clinicas?|historias?\s+clinicas?)",
        ),
        senal(
            "categorias_de_informacion_clinica",
            r"(?:informacion|registros?)\s+clinicos?|"
            r"(?:grabaciones?|archivos?)\s+de\s+audio|"
            r"notas.{0,35}transcripciones.{0,35}diagnosticos",
        ),
    ),
    senales_parciales=(
        senal("mencion_datos_usuario", r"datos\s+(?:del|de\s+los)\s+usuarios?"),
        senal(
            "mencion_informacion_usuario",
            r"informacion\s+(?:del|de\s+los)\s+usuarios?",
        ),
        senal(
            "mencion_generica_datos",
            r"(?:usar|usara|utilizar|utilizara|procesar|procesara)\s+"
            r"(?:los\s+)?datos",
        ),
        senal(
            "cita_normativa_de_datos_personales",
            r"datos\s+personales\s+y\s+(?:a\s+la\s+libre\s+circulaci[oó]n|"
            r"garantia)",
        ),
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
            r"(?:(?:se\s+limitaran|se\s+restringiran|solo\s+se\s+usaran|"
            r"unicamente\s+se\s+utilizaran)\s+(?:a\s+)?(?:variables|datos)"
            r"\s+(?:estrictamente\s+)?necesari[oa]s|(?:excluir[a]?|"
            r"se\s+excluiran)\s+(?:variables|datos)\s+no\s+necesari[oa]s)"
            r"\s+para\s+(?:la\s+)?(?:finalidad|objetivo|proposito)",
        ),
        senal(
            "prohibicion_de_uso_para_fin_distinto",
            r"(?:no\s+se\s+podra|no\s+podra|no\s+se\s+(?:utilizara|"
            r"usara|proporcionara)).{0,90}(?:datos|informacion)"
            r".{0,90}(?:finalidades?|fines?)\s+distint[oa]s?\s+a"
            r"(?:\s+aquell[oa]s)?.{0,60}(?:recogid[oa]s?|recabad[oa]s?|"
            r"obtenid[oa]s?|recopilad[oa]s?)",
        ),
        senal(
            "datos_vinculados_a_finalidad",
            r"(?:datos|informacion|variables).{0,60}"
            r"(?:para|con\s+el\s+fin\s+de|con\s+la\s+finalidad\s+de)\s+"
            r"(?:entrenar|validar|calcular|generar|predecir|clasificar|"
            r"recomendar|detectar|evaluar|priorizar)",
        ),
        senal(
            "imagen_clinica_vinculada_a_diagnostico",
            r"imagenes?\s+clinicas?.{0,100}diagnostico|"
            r"diagnostico.{0,100}imagenes?\s+clinicas?",
        ),
        senal(
            "finalidad_antes_de_los_datos",
            r"(?:calculo|calcular|evaluacion|evaluar|clasificacion|"
            r"clasificar|prediccion|predecir).{0,80}"
            r"(?:a\s+partir\s+de|mediante)\s+datos\s+"
            r"(?:financieros|crediticios|clinicos|personales)",
        ),
        senal(
            "informacion_clinica_vinculada_a_procesamiento",
            r"(?:audio|grabaciones?|transcripciones?|notas\s+clinicas?|"
            r"informacion\s+clinica).{0,100}(?:para\s+(?:su\s+)?|"
            r"mediante\s+)(?:almacenamiento|procesamiento|analisis|"
            r"transcripcion|diagnostico)",
        ),
    ),
    senales_parciales=(
        senal(
            "mencion_finalidad",
            r"finalidad(?:es)?\s+(?:de\s+uso|del\s+tratamiento|de\s+los\s+datos)",
        ),
        senal("mencion_uso_datos", r"uso\s+de\s+(?:los\s+)?datos"),
        senal(
            "mencion_minimizacion",
            r"variables\s+necesarias|minimizacion\s+de\s+datos",
        ),
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
            r"(?:datos|dataset|registros|fuentes).{0,90}"
            r"(?:ultimos?|periodo\s+de)\s+\d+\s+mes(?:es)?",
        ),
        senal(
            "criterio_cuantificado_de_calidad",
            r"(?:calidad|completitud|cobertura|precision).{0,35}"
            r"(?:\d+(?:[.,]\d+)?\s*%|umbral|criterio\s+de\s+aceptacion)",
        ),
        senal(
            "frecuencia_de_actualizacion",
            r"(?:datos|dataset).{0,60}(?:se\s+actualizaran|actualizacion)"
            r".{0,35}(?:mensual|trimestral|semestral|anual)(?:mente)?|"
            r"(?:datos|dataset).{0,60}(?:se\s+actualizaran|actualizacion)"
            r".{0,35}cada\s+\d+",
        ),
    ),
    senales_parciales=(
        senal("mencion_calidad", r"calidad\s+(?:de\s+los?\s+)?datos?"),
        senal("mencion_completitud", r"completitud|datos\s+completos"),
        senal("mencion_cobertura", r"cobertura\s+(?:de\s+los?\s+)?datos?"),
        senal("mencion_representatividad", r"representativ[oa]s?"),
        senal(
            "mencion_actualizacion_datos",
            r"actualizacion\s+de\s+datos|datos.{0,20}actualizar",
        ),
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
            r"(?:roles?|responsables?|personal|equipo|administradores?|"
            r"analistas?)\s+(?:autorizad[oa]s?|designad[oa]s?)?.{0,25}"
            r"(?:podr[aá]n?\s+acceder|con\s+acceso|tendr[aá]n?\s+acceso)"
            r".{0,40}(?:datos|dataset|informacion)",
        ),
        senal(
            "control_de_acceso_especifico",
            r"control(?:es)?\s+de\s+acceso\s+(?:basad[oa]\s+en|por)\s+rol",
        ),
        senal(
            "proteccion_tecnica_especifica",
            r"(?:cifrad[oa]s?|encriptad[oa]s?).{0,30}"
            r"(?:en\s+reposo|en\s+transito|aes|tls)",
        ),
        senal(
            "rol_de_seguridad_con_control_de_acceso",
            r"(?:ingenier[oa]|especialista|responsable|administrador)"
            r".{0,80}(?:seguridad|protecci[oó]n).{0,140}"
            r"(?:establecer|definir|gestionar|implementar)\w*.{0,50}"
            r"controles?\s+de\s+acceso.{0,45}(?:modelos?|datos|"
            r"informaci[oó]n)",
        ),
        senal(
            "autenticacion_de_usuarios_autorizados",
            r"(?:control\s+de\s+)?autenticacion\s+de\s+acceso\s+para\s+"
            r"usuarios\s+(?:autorizados|establecidos)",
        ),
    ),
    senales_parciales=(
        senal("mencion_acceso", r"acceso\s+a\s+(?:los\s+)?datos"),
        senal("mencion_seguridad_generica", r"datos\s+(?:estaran\s+)?seguros?"),
        senal("mencion_proteccion_generica", r"datos\s+(?:estaran\s+)?protegidos?"),
        senal(
            "proteccion_o_confidencialidad_de_datos",
            r"(?:proteccion|proteger|confidencialidad).{0,70}datos|"
            r"datos.{0,70}(?:proteccion|proteger|confidencialidad)",
        ),
        senal(
            "proteccion_de_datos_mediante_cifrado",
            r"(?:proteger|proteccion|confidencialidad).{0,70}"
            r"datos.{0,70}cifrad\w*|datos.{0,70}"
            r"(?:confidencialidad|cifrad\w*)",
        ),
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
            r"(?:plazo|periodo)\s+de\s+(?:retencion|conservacion)\s+de\s+"
            r"\d+\s*(?:dias|meses|anos)?",
        ),
        senal(
            "eliminacion_condicionada",
            r"(?:eliminaran|borraran|anonimizaran).{0,50}"
            r"(?:despues|tras|cuando|al\s+finalizar|en\s+un\s+plazo)",
        ),
        senal(
            "destruccion_o_borrado_irrecuperable_condicionado",
            r"(?:(?:una\s+vez\s+finalizado|al\s+finalizar|tras\s+la\s+"
            r"finalizacion|cuando|si|despues\s+de).{0,120}"
            r"(?:destruccion|borrado\s+irrecuperable)|"
            r"(?:destruccion|borrado\s+irrecuperable).{0,120}"
            r"(?:ya\s+no\s+deba|no\s+deba|deje\s+de|haya\s+finalizado|"
            r"una\s+vez\s+finalizado|al\s+finalizar))",
        ),
        senal(
            "eliminacion_definitiva_a_solicitud",
            r"eliminar\w*.{0,35}forma\s+definitiva.{0,80}"
            r"(?:cuando|a\s+solicitud|si).{0,45}"
            r"(?:paciente|usuario|titular|sea\s+requerido)",
        ),
    ),
    senales_parciales=(
        senal("mencion_retencion", r"retenci[oó]n\s+de\s+datos"),
        senal("mencion_eliminacion", r"eliminaci[oó]n\s+de\s+datos"),
        senal("mencion_anonimizacion", r"anonimizaci[oó]n"),
        senal(
            "conservacion_sujeta_a_normativa",
            r"(?:datos|resultados?|informacion).{0,45}"
            r"(?:conservaran|retendran|almacenaran).{0,80}normativa",
        ),
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
            r"base\s+legal\s+(?:para|de)\s+(?:el\s+)?tratamiento",
        ),
        senal(
            "trazabilidad_del_uso",
            r"(?:registrar|registrara|mantendra).{0,45}"
            r"(?:accesos|uso\s+de\s+datos|datos\s+utilizados|"
            r"fuente\s+de\s+datos|version\s+del\s+dataset)",
        ),
    ),
    senales_parciales=(
        senal("mencion_consentimiento", r"consentimiento"),
        senal("mencion_privacidad_generica", r"privacidad\s+de\s+los?\s+datos"),
        senal(
            "mencion_confidencialidad_datos",
            r"confidencialidad.{0,50}datos|datos.{0,50}confidencialidad",
        ),
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
            r"(?:reportar|reportara|medir|medira|evaluar|evaluara)\s+"
            r"(?:el\s+)?(?:desempeno|precision|tasa\s+de\s+error|"
            r"falsos\s+negativos|falsos\s+positivos)\s+por\s+"
            r"(?:grupo|subgrupo|subpoblacion)",
        ),
        senal(
            "umbral_diferencia_subgrupos",
            r"diferencia\s+de\s+\w+\s+entre\s+subgrupos\s+"
            r"supera\s+(?:el\s+)?umbral",
        ),
        senal(
            "riesgo_desigual_especificado",
            r"(?:riesgo|diferencia|brecha).{0,45}"
            r"(?:sesgo|discriminacion|trato\s+desigual|error\s+desigual)",
        ),
        senal(
            "prevencion_explicita_de_sesgos",
            r"(?:decisiones?\s+tomadas?\s+por\s+(?:la\s+)?ia|"
            r"sistemas?\s+de\s+ia).{0,120}"
            r"(?:no\s+perpetu\w*|no\s+gener\w*|evit\w*|preven\w*)"
            r".{0,80}sesgos?",
        ),
        senal(
            "control_operativo_de_sesgos",
            r"(?:sistemas?|mecanismos?|guardarra[ií]les?)\s+"
            r"(?:fundamentales?\s+)?(?:de\s+)?control\s+de\s+sesgos?|"
            r"protocolos?\s+de\s+evaluaci[oó]n\s+de\s+sesgos?"
            r"(?:\s+y\s+fairness)?",
        ),
    ),
    senales_parciales=(
        senal("mencion_sesgos", r"sesgos?"),
        senal("mencion_equidad", r"equidad|equitativ[oa]s?"),
        senal("mencion_discriminacion", r"discriminaci[oó]n|discriminatori[oa]s?"),
        senal("mencion_trato_justo", r"result?ados?\s+justos?|trato\s+desigual"),
        senal(
            "exclusion_de_atributos_protegidos",
            r"no\s+deber[aá].{0,45}(?:genero|etnia|raza|sexo|"
            r"discapacidad).{0,70}(?:variable|decision)",
        ),
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
            r"(?:desempeno|precision|tasa\s+de\s+error).{0,30}por\s+"
            r"(?:grupo|subgrupo|subpoblacion).{0,30}"
            r"(?:etari[oa]|edad|genero|sexo|discapacidad|origen|zona)",
        ),
        senal(
            "subgrupos_definidos",
            r"por\s+(?:subgrupos?|subpoblaci(?:on|ones))\s+"
            r"(?:etari[oa]s?|de\s+genero|relevantes?)",
        ),
        senal(
            "grupos_concretos_identificados",
            r"(?:mujeres|hombres|personas\s+mayores|personas\s+con\s+"
            r"discapacidad|poblacion\s+rural|poblacion\s+urbana|"
            r"comunidades\s+indigenas).{0,45}(?:mujeres|hombres|"
            r"personas\s+mayores|personas\s+con\s+discapacidad|"
            r"poblacion\s+rural|poblacion\s+urbana|"
            r"comunidades\s+indigenas)",
        ),
    ),
    senales_parciales=(
        senal("mencion_grupos", r"grupos?\s+(?:afectad[oa]s|vulnerables?)"),
        senal("comparacion_generica_por_grupo", r"(?:por|entre)\s+grupos?"),
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
        senal(
            "atributos_protegidos_excluidos_de_decision",
            r"no\s+deber[aá].{0,45}(?:genero|etnia|raza|sexo|"
            r"discapacidad).{0,70}(?:variables?\s+de\s+decision|"
            r"para\s+(?:decidir|calcular|clasificar))",
        ),
        senal(
            "proxy_con_atributo_sensible",
            r"(?:codigo\s+postal|zona\s+geografica|apellido|idioma|"
            r"historial\s+laboral).{0,45}(?:proxy|sustitut[oa]).{0,45}"
            r"(?:origen|etnia|raza|genero|sexo|ingreso|discapacidad)",
        ),
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
            r"(?:tasa\s+de\s+)?(?:falsos\s+negativos|falsos\s+positivos|"
            r"precision|recall|tasa\s+de\s+error).{0,45}"
            r"(?:por|entre).{0,35}(?:grupos?|subgrupos?|subpoblaciones?|"
            r"mujeres|hombres)",
        ),
        senal(
            "prueba_por_subpoblacion_definida",
            r"prueba(?:s)?\s+por\s+subpoblaci(?:on|ones)",
        ),
        senal(
            "brecha_con_umbral_numerico",
            r"(?:diferencia|brecha).{0,45}\d+(?:[.,]\d+)?\s*"
            r"(?:%|puntos?|puntos\s+porcentuales).{0,35}"
            r"(?:entre|por).{0,35}(?:grupos?|subgrupos?|subpoblaciones?|"
            r"mujeres|hombres)",
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
            r"(?:activar|activara)\s+revision\s+(?:del\s+responsable\s+)?"
            r"(?:designado\s+)?si\s+la\s+diferencia",
        ),
        senal(
            "accion_condicionada_ante_brecha",
            r"(?:si|cuando|en\s+caso\s+de).{0,90}"
            r"(?:brecha|diferencia|sesgo|umbral).{0,130}"
            r"(?:suspendera|detendra|revisara|ajustara|reentrenara|"
            r"corregira|mitigara)",
        ),
        senal(
            "mecanismo_preventivo_de_sesgos",
            r"implementar\w*.{0,35}mecanismos?.{0,100}"
            r"(?:no\s+perpetu\w*|no\s+gener\w*|evit\w*|preven\w*)"
            r".{0,80}sesgos?",
        ),
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
            r"responsable\s+designado.{0,60}"
            r"(?:diferencia|brecha|sesgo|equidad|desviacion)",
        ),
        senal(
            "rol_encargado_de_revision",
            r"rol\s+(?:encargado|responsable)\s+de\s+revisar",
        ),
        senal(
            "responsable_con_accion_de_revision",
            r"(?:comite|equipo|responsable|auditor|area).{0,45}"
            r"(?:revisara|monitoreara|evaluara|investigara|actuara).{0,60}"
            r"(?:sesgo|equidad|brecha|diferencia|desempeno\s+por\s+grupo)",
        ),
        senal(
            "especialista_etico_responsable_de_sesgos",
            r"especialista\s+en\s+[eé]tica\s+y\s+cumplimiento\s+de\s+ia"
            r".{0,260}(?:evaluaci[oó]n\s+de\s+sesgos?|fairness|"
            r"auditor[ií]as?\s+[eé]ticas?)",
        ),
    ),
    senales_parciales=(
        senal(
            "mencion_responsable_generico",
            r"responsable\s+de\s+(?:la\s+)?revisi[oó]n",
        ),
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
            r"(?:de|ante)\s+(?:sesgos?|brechas?|cambios?\s+(?:en|de)\s+"
            r"(?:los?\s+)?(?:datos|contexto|poblacion))",
        ),
        senal(
            "revision_periodica_definida",
            r"revision\s+periodica\s+(?:de|ante)\s+(?:sesgos?|brechas?|"
            r"cambios?\s+(?:en|de)\s+(?:los?\s+)?(?:datos|contexto|"
            r"poblacion))",
        ),
    ),
    senales_parciales=(
        senal(
            "mencion_seguimiento",
            r"seguimiento\s+posterior.{0,50}"
            r"(?:sesgo|equidad|grupos?|subpoblaciones?)",
        ),
        senal(
            "mencion_monitoreo_generico",
            r"monitoreo.{0,50}(?:sesgo|equidad|grupos?|subpoblaciones?|"
            r"cambios?\s+(?:en|de)\s+(?:los?\s+)?(?:datos|contexto))",
        ),
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
