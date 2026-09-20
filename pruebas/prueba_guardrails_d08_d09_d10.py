"""Pruebas de robustez, accountability e impacto social y ambiental."""

from __future__ import annotations

from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    DimensionEtica,
    FamiliaGuardrail,
    NivelCobertura,
    SolicitudEvaluacionEtica,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_D08,
    GUARDRAILS_D08_D10,
    GUARDRAILS_D09,
    GUARDRAILS_D10,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto
from etica_ia_ers.rubrica_y_agregacion import calcular_cobertura_etica


_CODIGOS_ESPERADOS = (
    "GR-D08-PRES-ROBUSTEZ",
    "GR-D08-VERIF-METRICAS",
    "GR-D08-CTRL-FALLAS",
    "GR-D08-CTRL-CONTINGENCIA",
    "GR-D08-VERIF-MONITOREO",
    "GR-D08-RESP-INCIDENTES",
    "GR-D08-QUAL-DECLARATIVO",
    "GR-D09-PRES-RESPONSABLES",
    "GR-D09-RESP-ROLES",
    "GR-D09-VERIF-REGISTROS",
    "GR-D09-VERIF-VERSIONADO",
    "GR-D09-CTRL-RECLAMOS",
    "GR-D09-CTRL-REPARACION",
    "GR-D09-QUAL-DIFUSO",
    "GR-D10-PRES-IMPACTO",
    "GR-D10-DELIM-AFECTADOS",
    "GR-D10-VERIF-ACCESIBILIDAD",
    "GR-D10-CTRL-AUTONOMIA",
    "GR-D10-VERIF-SOSTENIBILIDAD",
    "GR-D10-CTRL-MITIGACION",
    "GR-D10-QUAL-GENERICO",
)


def _evaluar_texto(texto: str, *guardrails):
    resultado = analizar_texto(texto)
    motor = MotorEvaluacionEtica(RepositorioGuardrailsEnMemoria(guardrails))
    return motor.evaluar(
        SolicitudEvaluacionEtica(documento_id=uuid4(), resultado_nlp=resultado)
    )


def _nivel(resultado, codigo: str) -> NivelCobertura:
    for aplicacion in resultado.aplicaciones:
        if aplicacion.guardrail_codigo == codigo:
            assert aplicacion.hallazgo is not None
            return aplicacion.hallazgo.nivel_preliminar
    raise AssertionError(f"No se encontro aplicacion para {codigo}")


def prueba_catalogo_d08_d10_tiene_21_guardrails_sin_duplicados() -> None:
    codigos = [guardrail.definicion.codigo for guardrail in GUARDRAILS_D08_D10]
    assert tuple(codigos) == _CODIGOS_ESPERADOS
    assert len(codigos) == len(set(codigos))


@pytest.mark.parametrize(
    ("catalogo", "dimension"),
    (
        (GUARDRAILS_D08, DimensionEtica.D08),
        (GUARDRAILS_D09, DimensionEtica.D09),
        (GUARDRAILS_D10, DimensionEtica.D10),
    ),
)
def prueba_catalogos_estan_asociados_a_su_dimension(catalogo, dimension) -> None:
    assert all(dimension in guardrail.definicion.dimensiones for guardrail in catalogo)


@pytest.mark.parametrize(
    ("catalogo", "prefijo"),
    (
        (GUARDRAILS_D08, "D08"),
        (GUARDRAILS_D09, "D09"),
        (GUARDRAILS_D10, "D10"),
    ),
)
def prueba_catalogos_cubren_los_diez_criterios(catalogo, prefijo: str) -> None:
    criterios = {
        criterio
        for guardrail in catalogo
        for criterio in guardrail.definicion.criterios
    }
    assert criterios == {f"{prefijo}-C{numero}" for numero in range(1, 11)}


def prueba_catalogo_cubre_las_seis_familias() -> None:
    familias = {
        guardrail.definicion.familia for guardrail in GUARDRAILS_D08_D10
    }
    assert familias == set(FamiliaGuardrail)


def prueba_ejemplo_oficial_d08_declarativo_es_parcial() -> None:
    resultado = _evaluar_texto(
        "El sistema debera ser seguro, robusto y confiable.",
        *GUARDRAILS_D08,
    )

    assert _nivel(resultado, "GR-D08-PRES-ROBUSTEZ") == NivelCobertura.PARCIAL
    assert _nivel(resultado, "GR-D08-QUAL-DECLARATIVO") == NivelCobertura.PARCIAL


def prueba_ejemplo_oficial_d09_sin_evidencia_es_ausente() -> None:
    resultado = _evaluar_texto(
        "El sistema emitira recomendaciones automaticas para priorizar solicitudes.",
        *GUARDRAILS_D09,
    )

    assert all(
        aplicacion.hallazgo is not None
        and aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
        for aplicacion in resultado.aplicaciones
    )


def prueba_ejemplo_oficial_d10_declarativo_es_parcial() -> None:
    resultado = _evaluar_texto(
        "El sistema debera ser inclusivo y sostenible.",
        *GUARDRAILS_D10,
    )

    assert _nivel(resultado, "GR-D10-PRES-IMPACTO") == NivelCobertura.PARCIAL
    assert _nivel(resultado, "GR-D10-QUAL-GENERICO") == NivelCobertura.PARCIAL


def prueba_ejemplo_oficial_combinado_detecta_evidencia_explicita() -> None:
    texto = (
        "El sistema no debera emitir recomendaciones cuando reciba datos "
        "incompletos en variables criticas o cuando la confianza estimada sea "
        "inferior al umbral definido para el dominio. Cada incidente debera "
        "registrarse con fecha, responsable, version del modelo, motivo de "
        "interrupcion y accion tomada. El sistema debera considerar criterios "
        "de accesibilidad para operadores y revisar semestralmente el consumo "
        "computacional asociado a inferencias masivas."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D08_D10)

    for codigo in (
        "GR-D08-VERIF-METRICAS",
        "GR-D08-CTRL-FALLAS",
        "GR-D09-PRES-RESPONSABLES",
        "GR-D09-VERIF-REGISTROS",
        "GR-D09-VERIF-VERSIONADO",
        "GR-D10-VERIF-ACCESIBILIDAD",
        "GR-D10-VERIF-SOSTENIBILIDAD",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


def prueba_disponibilidad_de_infraestructura_sin_contexto_ia_es_ausente() -> None:
    texto = (
        "3.1. El sistema debera garantizar una disponibilidad del 99% "
        "durante el horario de atencion.\n"
        "3.2. El sistema debera responder cada consulta en menos de tres "
        "segundos."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D08[1])
    assert _nivel(resultado, "GR-D08-VERIF-METRICAS") == NivelCobertura.AUSENTE


def prueba_metrica_de_modelo_ia_sin_contexto_extra_es_explicita() -> None:
    texto = (
        "3.1. La precision del modelo debera ser superior al umbral "
        "definido antes de su despliegue."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D08[1])
    assert _nivel(resultado, "GR-D08-VERIF-METRICAS") == NivelCobertura.EXPLICITO


def prueba_numero_suelto_sin_porcentaje_no_certifica_umbral() -> None:
    texto = (
        "3.1. El sistema debera seguir el enfoque de medicina 6P, con "
        "precision, personalizacion y proactividad como pilares."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D08[1])
    assert _nivel(resultado, "GR-D08-VERIF-METRICAS") != NivelCobertura.EXPLICITO


def prueba_precision_con_porcentaje_si_certifica_umbral() -> None:
    texto = "3.1. La precision del modelo debera superar el 95%."
    resultado = _evaluar_texto(texto, GUARDRAILS_D08[1])
    assert _nivel(resultado, "GR-D08-VERIF-METRICAS") == NivelCobertura.EXPLICITO


def prueba_disponibilidad_de_ia_con_contexto_de_modelo_es_explicita() -> None:
    texto = (
        "3.1. La disponibilidad del modelo de inteligencia artificial "
        "debera superar el umbral minimo definido."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D08[1])
    assert _nivel(resultado, "GR-D08-VERIF-METRICAS") == NivelCobertura.EXPLICITO


def prueba_metrica_y_porcentaje_de_otro_enunciado_no_se_asocian() -> None:
    texto = (
        "La precision se documentara solamente como atributo informativo "
        "del modelo. La infraestructura general debera alcanzar una "
        "disponibilidad del 99%."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D08[1])
    assert _nivel(resultado, "GR-D08-VERIF-METRICAS") != NivelCobertura.EXPLICITO


def prueba_metrica_de_ia_se_detecta_despues_de_una_introduccion_larga() -> None:
    texto = (
        "Antecedentes generales del proyecto y alcance contractual. " * 7
        + "La disponibilidad del modelo de inteligencia artificial debera "
        "superar el 99%."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D08[1])
    assert _nivel(resultado, "GR-D08-VERIF-METRICAS") == NivelCobertura.EXPLICITO


def prueba_d08_cubre_contingencia_monitoreo_e_incidentes() -> None:
    texto = (
        "Ante una falla se aplicara el plan de contingencia y el modo degradado. "
        "El drift debera monitorearse mensualmente y generar una alerta. "
        "El equipo de operaciones debera registrar y atender los incidentes. "
        "La robustez se verificara mediante pruebas y metricas."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D08)

    for codigo in (
        "GR-D08-CTRL-CONTINGENCIA",
        "GR-D08-VERIF-MONITOREO",
        "GR-D08-RESP-INCIDENTES",
        "GR-D08-QUAL-DECLARATIVO",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


def prueba_equipo_fisico_de_infraestructura_no_es_evidencia_de_rol() -> None:
    texto = (
        "3.1. La solucion garantizara alta disponibilidad implementando "
        "mecanismos de redundancia dentro de un equipo fisico ubicado en "
        "el Centro de Proceso de Datos."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D09[1])
    assert _nivel(resultado, "GR-D09-RESP-ROLES") == NivelCobertura.AUSENTE


def prueba_rol_de_gobernanza_de_datos_sigue_siendo_explicito() -> None:
    texto = (
        "3.1. El responsable de datos debera revisar el cumplimiento "
        "normativo del modelo cada trimestre."
    )
    resultado = _evaluar_texto(texto, GUARDRAILS_D09[1])
    assert _nivel(resultado, "GR-D09-RESP-ROLES") == NivelCobertura.EXPLICITO


def prueba_d09_cubre_roles_reclamos_y_reparacion() -> None:
    texto = (
        "El auditor interno debera auditar los cambios y el equipo de operaciones "
        "gestionara el modelo. Los reclamos se presentaran mediante un portal con "
        "procedimiento, plazo y responsable. Ante una decision incorrecta se "
        "debera corregir la decision y notificar la correccion."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D09)

    for codigo in (
        "GR-D09-PRES-RESPONSABLES",
        "GR-D09-RESP-ROLES",
        "GR-D09-CTRL-RECLAMOS",
        "GR-D09-CTRL-REPARACION",
        "GR-D09-QUAL-DIFUSO",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


def prueba_d10_cubre_afectados_autonomia_y_mitigacion() -> None:
    texto = (
        "El impacto social sobre trabajadores y grupos vulnerables afectados "
        "por exclusion se revisara semestralmente. Los usuarios podran desactivar "
        "las recomendaciones para preservar su autonomia. El impacto ambiental "
        "se debera mitigar mediante una medida con responsable y seguimiento."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D10)

    for codigo in (
        "GR-D10-PRES-IMPACTO",
        "GR-D10-DELIM-AFECTADOS",
        "GR-D10-CTRL-AUTONOMIA",
        "GR-D10-CTRL-MITIGACION",
        "GR-D10-QUAL-GENERICO",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


@pytest.mark.parametrize(
    "texto",
    (
        "El usuario responsable podra registrar una nueva contrasena.",
        "El servidor cambiara a la version disponible.",
        "La aplicacion mostrara el consumo mensual de productos.",
        "El menu estara disponible desde la pantalla principal.",
        "El sistema guardara la fecha de actualizacion del perfil.",
    ),
)
def prueba_contextos_tecnicos_no_generan_evidencia_etica(texto: str) -> None:
    resultado = _evaluar_texto(texto, *GUARDRAILS_D08_D10)

    assert all(
        aplicacion.hallazgo is not None
        and aplicacion.hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
        for aplicacion in resultado.aplicaciones
    )


def prueba_deteccion_no_depende_de_mayusculas_ni_acentos() -> None:
    resultado = _evaluar_texto(
        "EL DRIFT DEBERA MONITOREARSE MENSUALMENTE Y GENERAR UNA ALERTA.",
        *GUARDRAILS_D08,
    )

    assert _nivel(resultado, "GR-D08-VERIF-MONITOREO") == NivelCobertura.EXPLICITO


def prueba_integra_catalogo_d08_d10_con_calculo_de_cobertura() -> None:
    resultado = _evaluar_texto(
        "Ante datos incompletos el sistema debera pausar la recomendacion. "
        "Cada incidente debera registrarse con fecha, responsable y motivo. "
        "El sistema debera aplicar criterios de accesibilidad para usuarios.",
        *GUARDRAILS_D08_D10,
    )

    cobertura = calcular_cobertura_etica(resultado)

    assert tuple(
        dimension.dimension for dimension in cobertura.resultados_por_dimension
    ) == (DimensionEtica.D08, DimensionEtica.D09, DimensionEtica.D10)
    assert cobertura.indicadores_guardrails.guardrails_aplicados == 21


@pytest.mark.parametrize(
    "guardrail",
    GUARDRAILS_D08_D10,
    ids=[guardrail.definicion.codigo for guardrail in GUARDRAILS_D08_D10],
)
def prueba_guardrails_sin_evidencia_son_ausentes(guardrail) -> None:
    resultado = _evaluar_texto(
        "El sistema debera mostrar un mensaje de bienvenida.",
        guardrail,
    )
    assert _nivel(resultado, guardrail.definicion.codigo) == NivelCobertura.AUSENTE


def prueba_reconoce_respuesta_a_anomalias_y_seguridad_desde_diseno() -> None:
    texto = (
        "La solucion aplicara seguridad desde el diseno basada en un analisis "
        "de riesgos. El operador debera detectar anomalias y problemas de "
        "funcionamiento y ponerles solucion de inmediato."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D08)

    assert _nivel(resultado, "GR-D08-CTRL-FALLAS") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D08-QUAL-DECLARATIVO") == (
        NivelCobertura.EXPLICITO
    )


def prueba_reconoce_registros_automaticos_y_actualizaciones_documentadas() -> None:
    texto = (
        "El servicio registrara automaticamente los eventos durante su ciclo "
        "de vida y conservara los archivos de registro durante la vigencia "
        "contractual. Todas las actualizaciones seran documentadas y comunicadas."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D09)

    assert _nivel(resultado, "GR-D09-VERIF-REGISTROS") == NivelCobertura.EXPLICITO
    assert _nivel(resultado, "GR-D09-VERIF-VERSIONADO") == NivelCobertura.PARCIAL


def prueba_reconoce_accesibilidad_autonomia_y_sostenibilidad_concretas() -> None:
    texto = (
        "La interfaz cumplira requisitos de accesibilidad y se validara con "
        "pruebas de usabilidad realizadas por personas usuarias representativas. "
        "Las personas podran revertir la informacion de salida. Se fijaran "
        "objetivos concretos para usar energia renovable y reducir la huella "
        "de carbono."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D10)

    for codigo in (
        "GR-D10-PRES-IMPACTO",
        "GR-D10-VERIF-ACCESIBILIDAD",
        "GR-D10-CTRL-AUTONOMIA",
        "GR-D10-VERIF-SOSTENIBILIDAD",
        "GR-D10-CTRL-MITIGACION",
    ):
        assert _nivel(resultado, codigo) == NivelCobertura.EXPLICITO


def prueba_coocurrencia_no_depende_de_la_posicion_en_fragmento() -> None:
    texto = (
        ("contexto operativo " * 60)
        + "Se definiran objetivos concretos para reducir la huella de carbono "
        "y utilizar fuentes de energia renovable."
    )
    resultado = _evaluar_texto(texto, *GUARDRAILS_D10)

    assert _nivel(resultado, "GR-D10-VERIF-SOSTENIBILIDAD") == (
        NivelCobertura.EXPLICITO
    )
