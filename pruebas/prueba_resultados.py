from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from etica_ia_ers.api import (
    app,
    obtener_repositorio,
    obtener_repositorio_guardrails,
)
from etica_ia_ers.dominio import (
    ContextoEvaluacionEtica,
    DecisionAplicabilidad,
    DefinicionGuardrail,
    DimensionEtica,
    EstadoAnalisis,
    EstadoGuardrail,
    EvaluacionPreliminarGuardrail,
    FamiliaGuardrail,
    NivelCobertura,
    PrioridadDocumental,
    ReferenciaEvidencia,
    TipoVinculoEvidencia,
)
from etica_ia_ers.modelo_etico_y_guardrails import RepositorioGuardrailsEnMemoria
from etica_ia_ers.persistencia_y_trazabilidad import RepositorioEnMemoria

DIRECTORIO_ERS = Path(__file__).resolve().parent.parent / "ejemplos" / "ers"


class GuardrailSintetico:
    """Guardrail de prueba: siempre EXPLICITO sobre el primer fragmento."""

    def __init__(self, codigo: str, dimension: DimensionEtica) -> None:
        self.definicion = DefinicionGuardrail(
            codigo=codigo,
            nombre=f"Guardrail sintetico {codigo}",
            version=1,
            estado=EstadoGuardrail.ACTIVA,
            familia=FamiliaGuardrail.PRESENCIA,
            dimensiones=(dimension,),
            descripcion="Guardrail usado exclusivamente por las pruebas de API.",
            prioridad_base=PrioridadDocumental.MEDIA,
        )

    def decidir_aplicabilidad(
        self, contexto: ContextoEvaluacionEtica
    ) -> DecisionAplicabilidad:
        return DecisionAplicabilidad(aplica=True, motivo="Aplica siempre en la prueba.")

    def evaluar(
        self, contexto: ContextoEvaluacionEtica
    ) -> EvaluacionPreliminarGuardrail:
        fragmento = contexto.resultado_nlp.fragmentos_clasificados[0].fragmento
        return EvaluacionPreliminarGuardrail(
            nivel=NivelCobertura.EXPLICITO,
            justificacion="Evidencia sintetica encontrada en el primer fragmento.",
            prioridad=PrioridadDocumental.MEDIA,
            justificacion_prioridad="Prioridad fija de la prueba.",
            evidencias=(
                ReferenciaEvidencia(
                    fragmento_id=fragmento.id,
                    tipo_vinculo=TipoVinculoEvidencia.SOPORTA,
                ),
            ),
        )


@pytest.fixture
def entorno_api() -> Iterator[Tuple[TestClient, RepositorioEnMemoria]]:
    repositorio = RepositorioEnMemoria()
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    app.dependency_overrides[obtener_repositorio_guardrails] = (
        lambda: RepositorioGuardrailsEnMemoria(
            (GuardrailSintetico("GR-PRUEBA-API-01", DimensionEtica.D01),)
        )
    )
    try:
        with TestClient(app) as cliente:
            yield cliente, repositorio
    finally:
        app.dependency_overrides.clear()


def _cargar_documento(cliente: TestClient, texto: bytes) -> UUID:
    respuesta = cliente.post(
        "/documentos",
        files={"archivo": ("ers.txt", texto, "text/plain")},
    )
    assert respuesta.status_code == 201
    return UUID(respuesta.json()["documento_id"])


def prueba_resultados_informa_documento_no_encontrado(entorno_api) -> None:
    cliente, _ = entorno_api

    respuesta = cliente.get(f"/documentos/{uuid4()}/resultados")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Documento no encontrado."


def prueba_resultados_evalua_documento_y_arma_reporte_completo(entorno_api) -> None:
    cliente, repositorio = entorno_api
    documento_id = _cargar_documento(
        cliente, b"1.1. El sistema debera registrar cada decision automatizada."
    )

    respuesta = cliente.get(f"/documentos/{documento_id}/resultados")

    assert respuesta.status_code == 200
    datos = respuesta.json()

    assert datos["metadatos"]["documento_id"] == str(documento_id)
    assert datos["metadatos"]["estado"] == EstadoAnalisis.EVALUADO.value

    # Se genera una entrada para cada dimension. Las que no fueron evaluadas
    # no se convierten artificialmente en AUSENTE.
    dimensiones = {r["dimension_codigo"] for r in datos["resultados_dimension"]}
    assert dimensiones == {f"D{n:02d}" for n in range(1, 11)}

    resultado_d01 = next(
        r for r in datos["resultados_dimension"] if r["dimension_codigo"] == "D01"
    )
    assert resultado_d01["nivel_consolidado"] == NivelCobertura.EXPLICITO.value
    assert resultado_d01["resultado_dimension_id"] is not None
    assert len(resultado_d01["hallazgos_relacionados"]) == 1

    resultado_d02 = next(
        r for r in datos["resultados_dimension"] if r["dimension_codigo"] == "D02"
    )
    assert resultado_d02["nivel_consolidado"] is None
    assert resultado_d02["resultado_dimension_id"] is None
    assert resultado_d02["valor_auxiliar"] is None
    assert resultado_d02["prioridad_documental"] is None
    assert resultado_d02["hallazgos_relacionados"] == []

    assert len(datos["hallazgos"]) == 1
    hallazgo = datos["hallazgos"][0]
    assert hallazgo["guardrail_codigo"] == "GR-PRUEBA-API-01"
    assert hallazgo["nivel_preliminar"] == NivelCobertura.EXPLICITO.value
    assert hallazgo["valor_auxiliar"] == 2
    assert len(hallazgo["evidencias"]) == 1
    assert hallazgo["evidencias"][0]["tipo_vinculo"] == (
        TipoVinculoEvidencia.SOPORTA.value
    )

    indicadores = datos["indicadores"]
    assert indicadores["total_dimensiones"] == 10
    assert indicadores["dimensiones_explicitas"] == 1
    assert indicadores["dimensiones_ausentes"] == 0
    assert indicadores["total_hallazgos"] == 1
    assert indicadores["total_alertas"] == 0
    assert indicadores["total_recomendaciones"] == 0
    assert indicadores["recomendaciones_alta_prioridad"] == 0
    assert len(indicadores["por_grupo"]) == 4
    assert {grupo["grupo_tematico"] for grupo in indicadores["por_grupo"]} == {
        "Contexto y afectados",
        "Datos y trato justo",
        "Comprensión y control humano",
        "Gobernanza y operación responsable",
    }

    assert datos["lectura_global"]
    assert datos["resumen_ejecutivo"]
    assert datos["alertas"] == []
    assert datos["recomendaciones"] == []
    assert "no constituyen una certificacion etica" not in datos["resumen_ejecutivo"]

    # El endpoint deja el documento marcado como evaluado para consultas
    # posteriores de estado.
    registro = repositorio.obtener(documento_id)
    assert registro.estado is EstadoAnalisis.EVALUADO

    estado = cliente.get(f"/documentos/{documento_id}/estado")
    assert estado.json()["estado"] == EstadoAnalisis.EVALUADO.value


def prueba_resultados_es_reproducible_entre_llamadas(entorno_api) -> None:
    cliente, _ = entorno_api
    documento_id = _cargar_documento(
        cliente, b"1.1. El sistema debera registrar cada decision automatizada."
    )

    primera = cliente.get(f"/documentos/{documento_id}/resultados").json()
    segunda = cliente.get(f"/documentos/{documento_id}/resultados").json()

    assert primera["lectura_global"] == segunda["lectura_global"]
    assert primera["indicadores"] == segunda["indicadores"]
    assert len(primera["hallazgos"]) == len(segunda["hallazgos"])
    # Cada evaluacion es una ejecucion nueva: el identificador de analisis
    # cambia aunque el contenido evaluado sea el mismo.
    assert (
        primera["metadatos"]["analisis_id"] != segunda["metadatos"]["analisis_id"]
    )


@pytest.mark.parametrize(
    "nombre_archivo",
    [
        "scoring_crediticio.txt",
        "diagnostico_medico.txt",
        "sistema_recomendador.txt",
    ],
)
def prueba_resultados_integra_pipeline_real_sobre_ers_de_ejemplo(
    nombre_archivo: str,
) -> None:
    """Integracion con los guardrails reales (D01-D04), sin overrides."""
    repositorio = RepositorioEnMemoria()
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    try:
        with TestClient(app) as cliente:
            contenido = (DIRECTORIO_ERS / nombre_archivo).read_bytes()
            documento_id = _cargar_documento(cliente, contenido)

            respuesta = cliente.get(f"/documentos/{documento_id}/resultados")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos["resultados_dimension"]) == 10
    assert datos["indicadores"]["total_hallazgos"] > 0
    assert datos["indicadores"]["total_alertas"] == len(datos["alertas"])
    assert datos["indicadores"]["total_recomendaciones"] == len(
        datos["recomendaciones"]
    )
    assert len(datos["alertas"]) <= 10
    recomendaciones = {
        recomendacion["recomendacion_id"]: recomendacion
        for recomendacion in datos["recomendaciones"]
    }
    for alerta in datos["alertas"]:
        assert alerta["resultado_dimension_id"]
        assert alerta["hallazgos_relacionados"]
        assert len(alerta["recomendaciones_asociadas"]) == 1
        assert alerta["recomendaciones_asociadas"][0] in recomendaciones
    assert datos["lectura_global"] in {
        "Cobertura documental insuficiente",
        "Cobertura documental inicial",
        "Cobertura documental desarrollada",
    }


def prueba_diagnostico_medico_conserva_evidencia_y_brechas() -> None:
    repositorio = RepositorioEnMemoria()
    app.dependency_overrides[obtener_repositorio] = lambda: repositorio
    try:
        with TestClient(app) as cliente:
            contenido = (DIRECTORIO_ERS / "diagnostico_medico.txt").read_bytes()
            documento_id = _cargar_documento(cliente, contenido)
            respuesta = cliente.get(f"/documentos/{documento_id}/resultados")
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 200
    datos = respuesta.json()
    niveles = {
        resultado["dimension_codigo"]: resultado["nivel_consolidado"]
        for resultado in datos["resultados_dimension"]
    }
    assert niveles == {
        "D01": "PARCIAL",
        "D02": "PARCIAL",
        "D03": "PARCIAL",
        "D04": "AUSENTE",
        "D05": "AUSENTE",
        "D06": "PARCIAL",
        "D07": "PARCIAL",
        "D08": "PARCIAL",
        "D09": "AUSENTE",
        "D10": "AUSENTE",
    }

    hallazgos_con_evidencia = {
        hallazgo["guardrail_codigo"]: hallazgo
        for hallazgo in datos["hallazgos"]
        if hallazgo["nivel_preliminar"] != "AUSENTE"
    }
    for codigo in (
        "GR-D01-DELIM-USOS",
        "GR-D01-VERIF-LIMITACIONES",
        "GR-D02-PRES-ACTORES",
        "GR-D03-PRES-DATOS",
        "GR-D03-RESP-ACCESO",
        "GR-D03-CTRL-RETENCION",
        "GR-D06-PRES-EXPLICACION",
        "GR-D07-PRES-HUMANO",
        "GR-D07-DELIM-ROLES",
        "GR-D07-CTRL-INTERVENCION",
        "GR-D08-VERIF-METRICAS",
    ):
        assert codigo in hallazgos_con_evidencia
        assert hallazgos_con_evidencia[codigo]["evidencias"]

    assert datos["indicadores"]["dimensiones_parciales"] == 6
    assert datos["indicadores"]["dimensiones_ausentes"] == 4
    assert datos["indicadores"]["porcentaje_cobertura_no_ausente"] == 60.0
