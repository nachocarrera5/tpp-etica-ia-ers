"""Pruebas de los guardrails especificos por dominio de aplicacion."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from etica_ia_ers.api import app
from etica_ia_ers.dominio import (
    DefinicionGuardrail,
    DimensionEtica,
    DominioAplicacion,
    EstadoAplicacionGuardrail,
    EstadoGuardrail,
    FamiliaGuardrail,
    NivelCobertura,
    PrioridadDocumental,
    SolicitudEvaluacionEtica,
    resolver_dominio_aplicacion,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GR_D03_DELIM_EDU_DATOS,
    GR_D03_DELIM_SALUD_CONSENTIMIENTO,
    GR_D04_DELIM_CRED_VARIABLES,
    GR_D04_DELIM_EDU_EQUIDAD,
    GR_D04_VERIF_EMP_DISCRIMINACION,
    GR_D05_PRES_EMP_INFORMACION,
    GR_D05_PRES_PUB_TRANSPARENCIA,
    GR_D05_PRES_REC_AVISO,
    GR_D06_VERIF_CRED_MOTIVOS,
    GR_D07_CTRL_EDU_DOCENTE,
    GR_D07_CTRL_EMP_DECISION,
    GR_D07_CTRL_REC_PERSONALIZACION,
    GR_D07_CTRL_SALUD_DECISION,
    GR_D08_VERIF_SALUD_VALIDACION,
    GR_D09_CTRL_CRED_IMPUGNACION,
    GR_D09_CTRL_PUB_RECURSO,
    GR_D10_CTRL_PUB_CANAL,
    GR_D10_CTRL_REC_MENORES,
    GUARDRAILS_ACTIVOS,
    GUARDRAILS_GENERALES,
    GUARDRAILS_POR_DOMINIO,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto
from etica_ia_ers.resultados_y_presentacion import (
    FormatoExportacion,
    exportar_reporte,
    serializar_reporte_resultados,
)
from etica_ia_ers.rubrica_y_agregacion import calcular_cobertura_etica


DIRECTORIO_EJEMPLOS = Path(__file__).resolve().parents[1] / "ejemplos" / "ers"

_ABREVIATURAS_DOMINIO = {
    DominioAplicacion.CREDITICIO: "CRED",
    DominioAplicacion.SALUD: "SALUD",
    DominioAplicacion.EMPLEO: "EMP",
    DominioAplicacion.EDUCACION: "EDU",
    DominioAplicacion.SECTOR_PUBLICO: "PUB",
    DominioAplicacion.RECOMENDACION: "REC",
}


def _evaluar(texto: str, dominio, *guardrails):
    motor = MotorEvaluacionEtica(RepositorioGuardrailsEnMemoria(guardrails))
    metadatos = {} if dominio is None else {"dominio": dominio}
    return motor.evaluar(
        SolicitudEvaluacionEtica(
            documento_id=uuid4(),
            resultado_nlp=analizar_texto(texto),
            metadatos=metadatos,
        )
    )


def _aplicacion(resultado, codigo: str):
    for aplicacion in resultado.aplicaciones:
        if aplicacion.guardrail_codigo == codigo:
            return aplicacion
    raise AssertionError(f"No se encontro aplicacion para {codigo}")


def _nivel(resultado, codigo: str) -> NivelCobertura:
    aplicacion = _aplicacion(resultado, codigo)
    assert aplicacion.hallazgo is not None, aplicacion.motivo
    return aplicacion.hallazgo.nivel_preliminar


@pytest.mark.parametrize(
    ("declarado", "esperado"),
    (
        ("crediticio", DominioAplicacion.CREDITICIO),
        ("Finanzas", DominioAplicacion.CREDITICIO),
        ("Salud", DominioAplicacion.SALUD),
        ("  Médico ", DominioAplicacion.SALUD),
        ("empleo", DominioAplicacion.EMPLEO),
        ("Educación", DominioAplicacion.EDUCACION),
        ("sector_publico", DominioAplicacion.SECTOR_PUBLICO),
        ("Administracion publica", DominioAplicacion.SECTOR_PUBLICO),
        ("Contenidos", DominioAplicacion.RECOMENDACION),
        ("recomendacion", DominioAplicacion.RECOMENDACION),
        (DominioAplicacion.SALUD, DominioAplicacion.SALUD),
    ),
)
def prueba_resuelve_dominios_y_alias_conocidos(declarado, esperado) -> None:
    assert resolver_dominio_aplicacion(declarado) == esperado


@pytest.mark.parametrize(
    "declarado",
    ("", "otro", "Logística", "Logistica de salud animal", None, 3),
)
def prueba_dominios_desconocidos_no_se_resuelven(declarado) -> None:
    assert resolver_dominio_aplicacion(declarado) is None


def prueba_definicion_rechaza_dominios_repetidos() -> None:
    with pytest.raises(ValueError, match="dominios"):
        DefinicionGuardrail(
            codigo="GR-D01-PRES-PRUEBA",
            nombre="Guardrail de prueba",
            version=1,
            estado=EstadoGuardrail.ACTIVA,
            familia=FamiliaGuardrail.PRESENCIA,
            dimensiones=(DimensionEtica.D01,),
            descripcion="Guardrail usado exclusivamente por la prueba.",
            dominios=(DominioAplicacion.SALUD, DominioAplicacion.SALUD),
        )


def prueba_guardrail_general_aplica_a_cualquier_dominio() -> None:
    definicion = GUARDRAILS_GENERALES[0].definicion

    assert not definicion.es_especifico_de_dominio
    assert definicion.aplica_a_dominio(None)
    assert definicion.aplica_a_dominio(DominioAplicacion.SALUD)


def prueba_catalogo_por_dominio_tiene_tres_guardrails_por_dominio() -> None:
    codigos = [guardrail.definicion.codigo for guardrail in GUARDRAILS_POR_DOMINIO]
    assert len(codigos) == 18
    assert len(codigos) == len(set(codigos))

    por_dominio = {}
    for guardrail in GUARDRAILS_POR_DOMINIO:
        definicion = guardrail.definicion
        assert len(definicion.dominios) == 1
        por_dominio.setdefault(definicion.dominios[0], []).append(definicion)
    assert set(por_dominio) == set(DominioAplicacion)
    assert all(len(definiciones) == 3 for definiciones in por_dominio.values())


@pytest.mark.parametrize(
    "guardrail",
    GUARDRAILS_POR_DOMINIO,
    ids=lambda guardrail: guardrail.definicion.codigo,
)
def prueba_codigo_identifica_dimension_y_dominio(guardrail) -> None:
    definicion = guardrail.definicion
    _, dimension, _, dominio, _ = definicion.codigo.split("-", 4)

    assert dimension == definicion.dimensiones[0].value
    assert dominio == _ABREVIATURAS_DOMINIO[definicion.dominios[0]]
    assert definicion.requiere_revision_por_defecto
    assert definicion.estado == EstadoGuardrail.ACTIVA


def prueba_catalogo_activo_suma_generales_y_por_dominio() -> None:
    assert GUARDRAILS_ACTIVOS == GUARDRAILS_GENERALES + GUARDRAILS_POR_DOMINIO
    assert len(GUARDRAILS_GENERALES) == 72
    RepositorioGuardrailsEnMemoria(GUARDRAILS_ACTIVOS)


@pytest.mark.parametrize("dominio", (None, "otro", "empleo"))
def prueba_guardrail_de_otro_dominio_no_es_aplicable(dominio) -> None:
    resultado = _evaluar(
        "El sistema no deberá emitir un diagnóstico sin la validación de un "
        "profesional.",
        dominio,
        GR_D07_CTRL_SALUD_DECISION,
    )

    aplicacion = _aplicacion(resultado, "GR-D07-CTRL-SALUD-DECISION")
    assert aplicacion.estado == EstadoAplicacionGuardrail.NO_APLICABLE
    assert "salud" in aplicacion.motivo


_CASOS = (
    (
        GR_D06_VERIF_CRED_MOTIVOS,
        "crediticio",
        "El sistema deberá informar al solicitante los motivos principales "
        "del rechazo de su solicitud.",
        "El sistema deberá mostrar al analista los factores que influyeron "
        "en el puntaje.",
    ),
    (
        GR_D04_DELIM_CRED_VARIABLES,
        "crediticio",
        "El sistema no deberá utilizar el código postal ni la nacionalidad "
        "como variables de decisión.",
        "El modelo evitará la discriminación de los solicitantes.",
    ),
    (
        GR_D09_CTRL_CRED_IMPUGNACION,
        "crediticio",
        "El solicitante podrá impugnar la decisión crediticia y solicitar "
        "una revisión humana.",
        "Se habilitará un procedimiento de reconsideración.",
    ),
    (
        GR_D07_CTRL_SALUD_DECISION,
        "salud",
        "El sistema no deberá emitir un diagnóstico definitivo sin la "
        "validación de un profesional.",
        "El sistema se utilizará únicamente como apoyo a la decisión médica.",
    ),
    (
        GR_D08_VERIF_SALUD_VALIDACION,
        "salud",
        "El modelo deberá superar una validación clínica prospectiva con una "
        "sensibilidad mínima del 95%.",
        "El sistema deberá contar con evidencia clínica de su desempeño.",
    ),
    (
        GR_D03_DELIM_SALUD_CONSENTIMIENTO,
        "salud",
        "Se requerirá el consentimiento informado de cada paciente para el "
        "tratamiento de sus datos.",
        "El sistema deberá proteger la confidencialidad de los datos de los "
        "pacientes.",
    ),
    (
        GR_D05_PRES_REC_AVISO,
        "recomendacion",
        "El sistema deberá indicar al usuario por qué se le recomienda cada "
        "contenido.",
        "La plataforma promoverá la transparencia de las recomendaciones.",
    ),
    (
        GR_D07_CTRL_REC_PERSONALIZACION,
        "recomendacion",
        "El usuario podrá desactivar las recomendaciones personalizadas.",
        "El sistema deberá permitir que el usuario indique que no le "
        "interesa una recomendación.",
    ),
    (
        GR_D10_CTRL_REC_MENORES,
        "recomendacion",
        "El sistema no deberá recomendar contenidos no aptos a usuarios "
        "menores de edad.",
        "La plataforma ofrecerá un perfil infantil.",
    ),
    (
        GR_D05_PRES_EMP_INFORMACION,
        "empleo",
        "Se deberá informar a cada candidato que su postulación es evaluada "
        "por un sistema de inteligencia artificial.",
        "Los candidatos recibirán información sobre el proceso de selección.",
    ),
    (
        GR_D04_VERIF_EMP_DISCRIMINACION,
        "empleo",
        "Se realizará una auditoría de sesgo trimestral que compare las "
        "tasas de selección por género y edad.",
        "El sistema promoverá la igualdad de oportunidades.",
    ),
    (
        GR_D07_CTRL_EMP_DECISION,
        "empleo",
        "Ningún candidato podrá ser descartado sin una revisión humana del "
        "reclutador.",
        "El equipo de recursos humanos supervisará el funcionamiento del "
        "sistema.",
    ),
    (
        GR_D03_DELIM_EDU_DATOS,
        "educacion",
        "El uso de datos de menores requerirá la autorización de sus padres "
        "o tutores.",
        "El sistema procesará datos de los estudiantes.",
    ),
    (
        GR_D07_CTRL_EDU_DOCENTE,
        "educacion",
        "El docente deberá revisar y confirmar cada calificación sugerida "
        "por el sistema.",
        "Los docentes podrán consultar los informes generados.",
    ),
    (
        GR_D04_DELIM_EDU_EQUIDAD,
        "educacion",
        "Se deberá medir la precisión del sistema para estudiantes de zonas "
        "rurales y con discapacidad.",
        "El sistema promoverá la inclusión educativa.",
    ),
    (
        GR_D05_PRES_PUB_TRANSPARENCIA,
        "sector_publico",
        "El sistema se inscribirá en el registro público de algoritmos del "
        "organismo.",
        "La administración garantizará la transparencia ante la ciudadanía.",
    ),
    (
        GR_D09_CTRL_PUB_RECURSO,
        "sector_publico",
        "El ciudadano podrá interponer recurso contra la resolución emitida "
        "con apoyo del sistema.",
        "Se informará sobre los recursos administrativos disponibles.",
    ),
    (
        GR_D10_CTRL_PUB_CANAL,
        "sector_publico",
        "Se mantendrá un canal de atención presencial para quienes no "
        "utilicen el asistente.",
        "El organismo considerará la brecha digital.",
    ),
)


def prueba_los_casos_cubren_todo_el_catalogo_por_dominio() -> None:
    assert {caso[0] for caso in _CASOS} == set(GUARDRAILS_POR_DOMINIO)


@pytest.mark.parametrize(
    ("guardrail", "dominio", "explicito", "parcial"),
    _CASOS,
    ids=lambda valor: getattr(getattr(valor, "definicion", None), "codigo", ""),
)
def prueba_guardrail_de_dominio_gradua_la_evidencia(
    guardrail,
    dominio: str,
    explicito: str,
    parcial: str,
) -> None:
    codigo = guardrail.definicion.codigo

    assert _nivel(_evaluar(explicito, dominio, guardrail), codigo) == (
        NivelCobertura.EXPLICITO
    )
    assert _nivel(_evaluar(parcial, dominio, guardrail), codigo) == (
        NivelCobertura.PARCIAL
    )
    assert _nivel(
        _evaluar(
            "El sistema deberá responder en menos de dos segundos.",
            dominio,
            guardrail,
        ),
        codigo,
    ) == NivelCobertura.AUSENTE


@pytest.mark.parametrize(
    ("archivo", "dominio", "esperados"),
    (
        (
            "scoring_crediticio.txt",
            "crediticio",
            {
                "GR-D04-DELIM-CRED-VARIABLES": NivelCobertura.EXPLICITO,
                "GR-D06-VERIF-CRED-MOTIVOS": NivelCobertura.PARCIAL,
                "GR-D09-CTRL-CRED-IMPUGNACION": NivelCobertura.AUSENTE,
            },
        ),
        (
            "diagnostico_medico.txt",
            "salud",
            {
                "GR-D03-DELIM-SALUD-CONSENTIMIENTO": NivelCobertura.PARCIAL,
                "GR-D07-CTRL-SALUD-DECISION": NivelCobertura.EXPLICITO,
                "GR-D08-VERIF-SALUD-VALIDACION": NivelCobertura.AUSENTE,
            },
        ),
        (
            "sistema_recomendador.txt",
            "recomendacion",
            {
                "GR-D05-PRES-REC-AVISO": NivelCobertura.AUSENTE,
                "GR-D07-CTRL-REC-PERSONALIZACION": NivelCobertura.PARCIAL,
                "GR-D10-CTRL-REC-MENORES": NivelCobertura.EXPLICITO,
            },
        ),
    ),
)
def prueba_ers_de_ejemplo_activan_los_guardrails_de_su_dominio(
    archivo: str,
    dominio: str,
    esperados,
) -> None:
    texto = (DIRECTORIO_EJEMPLOS / archivo).read_text(encoding="utf-8")

    resultado = _evaluar(texto, dominio, *GUARDRAILS_POR_DOMINIO)

    for codigo, nivel in esperados.items():
        assert _nivel(resultado, codigo) == nivel
    no_aplicables = [
        aplicacion
        for aplicacion in resultado.aplicaciones
        if aplicacion.estado == EstadoAplicacionGuardrail.NO_APLICABLE
    ]
    assert len(no_aplicables) == 15


def prueba_guardrail_critico_de_dominio_participa_de_la_dimension() -> None:
    resultado = _evaluar(
        "El sistema deberá permitir que un profesional revise el resultado.",
        "salud",
        GR_D08_VERIF_SALUD_VALIDACION,
    )

    dimension = calcular_cobertura_etica(resultado).resultados_por_dimension[0]

    assert dimension.dimension == DimensionEtica.D08
    assert dimension.nivel_consolidado == NivelCobertura.AUSENTE
    assert dimension.prioridad_documental == PrioridadDocumental.ALTA
    assert dimension.guardrails_criticos_pendientes == (
        "GR-D08-VERIF-SALUD-VALIDACION",
    )


def prueba_motor_advierte_dominio_sin_guardrails_especificos() -> None:
    resultado = _evaluar(
        "El sistema deberá registrar cada decisión.",
        "Logística",
        *GUARDRAILS_POR_DOMINIO,
    )

    assert resultado.advertencias == (
        "El dominio declarado 'Logística' no tiene guardrails especificos en "
        "el catalogo; se aplicaron solo los guardrails generales.",
    )


@pytest.mark.parametrize("dominio", (None, "", "salud"))
def prueba_motor_no_advierte_sin_dominio_o_con_dominio_conocido(
    dominio,
) -> None:
    resultado = _evaluar(
        "El sistema deberá registrar cada decisión.",
        dominio,
        *GUARDRAILS_POR_DOMINIO,
    )

    assert resultado.advertencias == ()


def prueba_reporte_identifica_el_dominio_aplicado() -> None:
    resultado = _evaluar(
        "El sistema deberá registrar cada decisión.",
        "Finanzas",
        *GUARDRAILS_POR_DOMINIO,
    )

    reporte = serializar_reporte_resultados(resultado, "ers.txt")

    assert reporte["metadatos"]["dominio_declarado"] == "Finanzas"
    assert reporte["metadatos"]["dominio_aplicacion"] == "crediticio"
    contenido = exportar_reporte(reporte, FormatoExportacion.MARKDOWN).contenido
    assert (
        "| Dominio de aplicación | Crédito y finanzas (con guardrails "
        "específicos) |"
    ) in contenido


def prueba_reporte_distingue_dominio_sin_guardrails_especificos() -> None:
    resultado = _evaluar(
        "El sistema deberá registrar cada decisión.",
        "Logística",
        *GUARDRAILS_POR_DOMINIO,
    )

    reporte = serializar_reporte_resultados(resultado, "ers.txt")

    assert reporte["metadatos"]["dominio_aplicacion"] is None
    contenido = exportar_reporte(reporte, FormatoExportacion.HTML).contenido
    assert "Logística (sin guardrails específicos)" in contenido


def prueba_api_aplica_los_guardrails_del_dominio_declarado(monkeypatch) -> None:
    monkeypatch.setenv("MODO_PUBLICO", "true")
    with TestClient(app) as cliente:
        respuesta = cliente.post(
            "/analisis",
            files={
                "archivo": (
                    "ers.txt",
                    (DIRECTORIO_EJEMPLOS / "diagnostico_medico.txt").read_bytes(),
                    "text/plain",
                )
            },
            data={"metadatos": json.dumps({"dominio": "salud"})},
        )

    assert respuesta.status_code == 200
    resultado = respuesta.json()
    assert resultado["metadatos"]["dominio_aplicacion"] == "salud"
    assert resultado["indicadores"]["guardrails_aplicados"] == 75
    assert resultado["indicadores"]["guardrails_no_aplicables"] == 15
    codigos = {hallazgo["guardrail_codigo"] for hallazgo in resultado["hallazgos"]}
    assert "GR-D07-CTRL-SALUD-DECISION" in codigos
    assert "GR-D06-VERIF-CRED-MOTIVOS" not in codigos


def prueba_hallazgo_identifica_si_el_guardrail_es_de_dominio() -> None:
    resultado = _evaluar(
        "El sistema no deberá emitir un diagnóstico sin la validación de un "
        "profesional.",
        "salud",
        GUARDRAILS_GENERALES[0],
        GR_D07_CTRL_SALUD_DECISION,
    )

    reporte = serializar_reporte_resultados(resultado, "ers.txt")

    dominios = {
        hallazgo["guardrail_codigo"]: hallazgo["guardrail_dominios"]
        for hallazgo in reporte["hallazgos"]
    }
    assert dominios[GUARDRAILS_GENERALES[0].definicion.codigo] == []
    assert dominios["GR-D07-CTRL-SALUD-DECISION"] == ["salud"]
    contenido = exportar_reporte(reporte, FormatoExportacion.MARKDOWN).contenido
    assert "- **Dominio del guardrail:** Salud" in contenido
    assert "- **Dominio del guardrail:** General" in contenido
