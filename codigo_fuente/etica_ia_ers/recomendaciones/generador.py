from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from etica_ia_ers.dominio import (
    AlertaDocumental,
    DimensionEtica,
    NivelCobertura,
    RecomendacionDocumental,
    ResultadoAlertasYRecomendaciones,
    ResultadoCoberturaEtica,
    ResultadoDimensionEtica,
    ResultadoEvaluacionEtica,
    TipoMejora,
)

from .errores import ResultadosIncompatiblesError


@dataclass(frozen=True)
class _PlantillaDimension:
    version: str
    detalle: str


_PLANTILLAS = {
    DimensionEtica.D01: _PlantillaDimension(
        "D01-v1",
        "el proposito, el contexto de aplicacion, los usos previstos y no "
        "previstos, los supuestos y las limitaciones",
    ),
    DimensionEtica.D02: _PlantillaDimension(
        "D02-v1",
        "los actores directos e indirectos, los grupos afectados y los "
        "impactos positivos y negativos previsibles",
    ),
    DimensionEtica.D03: _PlantillaDimension(
        "D03-v1",
        "los datos utilizados, su finalidad, calidad, acceso, proteccion y "
        "condiciones de retencion",
    ),
    DimensionEtica.D04: _PlantillaDimension(
        "D04-v1",
        "los grupos y proxies relevantes, las metricas y umbrales de equidad, "
        "la revision responsable y las acciones de mitigacion",
    ),
    DimensionEtica.D05: _PlantillaDimension(
        "D05-v1",
        "como se comunica el uso de IA, a quienes, por que canal, en que "
        "momento y con que limites",
    ),
    DimensionEtica.D06: _PlantillaDimension(
        "D06-v1",
        "que salidas requieren explicacion, sus destinatarios, formato, nivel "
        "de detalle, utilidad y responsable",
    ),
    DimensionEtica.D07: _PlantillaDimension(
        "D07-v1",
        "las decisiones supervisadas, los roles, las condiciones de "
        "activacion, la autoridad de intervencion, el procedimiento y registro",
    ),
    DimensionEtica.D08: _PlantillaDimension(
        "D08-v1",
        "las metricas y umbrales operativos, la respuesta ante fallas, las "
        "contingencias, el monitoreo, los incidentes y sus responsables",
    ),
    DimensionEtica.D09: _PlantillaDimension(
        "D09-v1",
        "los responsables, registros, versionado y trazabilidad, junto con los "
        "mecanismos de reclamo, correccion y conservacion de evidencia",
    ),
    DimensionEtica.D10: _PlantillaDimension(
        "D10-v1",
        "los impactos sociales, laborales y ambientales, las personas "
        "afectadas, la accesibilidad, autonomia, sostenibilidad y mitigacion",
    ),
}


def generar_alertas_y_recomendaciones(
    resultado_evaluacion: ResultadoEvaluacionEtica,
    resultado_cobertura: ResultadoCoberturaEtica,
) -> ResultadoAlertasYRecomendaciones:
    """Genera mejoras documentales trazables sin emitir veredictos."""
    _validar_trazabilidad(resultado_evaluacion, resultado_cobertura)

    alertas = []
    recomendaciones = []
    resultados = {
        resultado.dimension: resultado
        for resultado in resultado_cobertura.resultados_por_dimension
    }
    for dimension in DimensionEtica:
        resultado = resultados.get(dimension)
        if (
            resultado is None
            or resultado.nivel_consolidado == NivelCobertura.EXPLICITO
        ):
            continue

        recomendacion = _crear_recomendacion(resultado)
        recomendaciones.append(recomendacion)
        alertas.append(
            _crear_alerta(
                resultado_cobertura.documento_id,
                resultado,
                recomendacion,
            )
        )

    return ResultadoAlertasYRecomendaciones(
        analisis_id=resultado_cobertura.analisis_id,
        documento_id=resultado_cobertura.documento_id,
        fecha_generacion=datetime.now(timezone.utc),
        alertas=tuple(alertas),
        recomendaciones=tuple(recomendaciones),
        advertencias=resultado_cobertura.advertencias,
    )


def _crear_recomendacion(
    resultado: ResultadoDimensionEtica,
) -> RecomendacionDocumental:
    plantilla = _PLANTILLAS[resultado.dimension]
    es_ausente = resultado.nivel_consolidado == NivelCobertura.AUSENTE
    verbo = "Incorporar" if es_ausente else "Precisar"
    tipo = TipoMejora.INCORPORAR if es_ausente else TipoMejora.PRECISAR
    return RecomendacionDocumental(
        analisis_id=resultado.analisis_id,
        resultado_dimension_id=resultado.id,
        dimension=resultado.dimension,
        hallazgos_relacionados=resultado.hallazgos_relacionados,
        accion_sugerida=(
            f"{verbo} en la ERS {plantilla.detalle}, mediante condiciones "
            "documentales concretas y revisables."
        ),
        fundamento=(
            f"La cobertura documental de {resultado.dimension.value} se "
            f"consolido como {resultado.nivel_consolidado.value}. "
            f"{resultado.justificacion}"
        ),
        prioridad_documental=resultado.prioridad_documental,
        tipo_mejora=tipo,
        plantilla_version=plantilla.version,
    )


def _crear_alerta(
    documento_id: UUID,
    resultado: ResultadoDimensionEtica,
    recomendacion: RecomendacionDocumental,
) -> AlertaDocumental:
    nivel = resultado.nivel_consolidado.value.lower()
    return AlertaDocumental(
        analisis_id=resultado.analisis_id,
        documento_id=documento_id,
        resultado_dimension_id=resultado.id,
        dimension=resultado.dimension,
        nivel_cobertura=resultado.nivel_consolidado,
        prioridad_documental=resultado.prioridad_documental,
        titulo=(
            f"Cobertura documental {nivel} en {resultado.dimension.value}: "
            f"{resultado.nombre_dimension}"
        ),
        descripcion=resultado.justificacion,
        brechas=resultado.brechas_principales,
        hallazgos_relacionados=resultado.hallazgos_relacionados,
        recomendaciones_asociadas=(recomendacion.id,),
        requiere_revision_humana=resultado.requiere_revision_humana,
        motivo_revision_humana=resultado.motivo_revision_humana,
    )


def _validar_trazabilidad(
    evaluacion: ResultadoEvaluacionEtica,
    cobertura: ResultadoCoberturaEtica,
) -> None:
    if (
        evaluacion.analisis_id != cobertura.analisis_id
        or evaluacion.documento_id != cobertura.documento_id
    ):
        raise ResultadosIncompatiblesError(
            "La evaluacion y la cobertura deben pertenecer al mismo analisis "
            "y documento."
        )

    hallazgos = {hallazgo.id: hallazgo for hallazgo in evaluacion.hallazgos}
    if len(hallazgos) != len(evaluacion.hallazgos):
        raise ResultadosIncompatiblesError(
            "La evaluacion contiene hallazgos duplicados."
        )

    dimensiones_vistas = set()
    resultados_ids = set()
    for resultado in cobertura.resultados_por_dimension:
        if resultado.analisis_id != cobertura.analisis_id:
            raise ResultadosIncompatiblesError(
                "Los resultados por dimension deben pertenecer al analisis."
            )
        if (
            resultado.dimension in dimensiones_vistas
            or resultado.id in resultados_ids
        ):
            raise ResultadosIncompatiblesError(
                "La cobertura contiene resultados por dimension duplicados."
            )
        dimensiones_vistas.add(resultado.dimension)
        resultados_ids.add(resultado.id)
        for hallazgo_id in resultado.hallazgos_relacionados:
            hallazgo = hallazgos.get(hallazgo_id)
            if hallazgo is None:
                raise ResultadosIncompatiblesError(
                    "La cobertura referencia un hallazgo inexistente."
                )
            if resultado.dimension not in hallazgo.dimensiones_asociadas:
                raise ResultadosIncompatiblesError(
                    "El hallazgo no pertenece a la dimension consolidada."
                )
