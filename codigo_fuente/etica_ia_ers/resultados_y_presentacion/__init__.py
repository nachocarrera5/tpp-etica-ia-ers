"""Resultados, indicadores y presentacion para revision humana."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from etica_ia_ers.dominio import DimensionEtica, NivelCobertura, ResultadoEvaluacionEtica
from etica_ia_ers.rubrica_y_agregacion import (
    MetadatosReporteAnalisis,
    ReporteAnalisis,
    ResultadoDimension,
    agregar,
)


def serializar_reporte_resultados(
    evaluacion: ResultadoEvaluacionEtica,
    nombre_documento: str,
) -> Dict[str, Any]:
    reporte = agregar(evaluacion)
    metadatos = reporte.metadatos
    return {
        "metadatos": {
            "analisis_id": str(metadatos.analisis_id),
            "documento_id": str(metadatos.documento_id),
            "nombre_documento": nombre_documento,
            "fecha_inicio": metadatos.fecha_inicio.isoformat(),
            "fecha_fin": metadatos.fecha_fin.isoformat(),
            "estado": metadatos.estado,
        },
        "resumen_ejecutivo": reporte.resumen_ejecutivo,
        "lectura_global": reporte.lectura_global,
        "indicadores": {
            "total_dimensiones": reporte.indicadores.total_dimensiones,
            "dimensiones_ausentes": reporte.indicadores.dimensiones_ausentes,
            "dimensiones_parciales": reporte.indicadores.dimensiones_parciales,
            "dimensiones_explicitas": reporte.indicadores.dimensiones_explicitas,
            "porcentaje_cobertura_explicita": reporte.indicadores.porcentaje_cobertura_explicita,
            "porcentaje_cobertura_no_ausente": reporte.indicadores.porcentaje_cobertura_no_ausente,
            "total_hallazgos": reporte.indicadores.total_hallazgos,
            "hallazgos_con_revision_humana": reporte.indicadores.hallazgos_con_revision_humana,
            "porcentaje_revision_humana": reporte.indicadores.porcentaje_revision_humana,
            "hallazgos_prioridad_alta": reporte.indicadores.hallazgos_prioridad_alta,
            "hallazgos_prioridad_media": reporte.indicadores.hallazgos_prioridad_media,
            "hallazgos_prioridad_baja": reporte.indicadores.hallazgos_prioridad_baja,
            "dimensiones_prioridad_alta": [d.value for d in reporte.indicadores.dimensiones_prioridad_alta],
            "por_grupo": [
                {
                    "grupo_tematico": grupo.grupo_tematico,
                    "dimensiones_incluidas": [d.value for d in grupo.dimensiones_incluidas],
                    "ausentes": grupo.ausentes,
                    "parciales": grupo.parciales,
                    "explicitas": grupo.explicitas,
                    "prioridad_maxima": grupo.prioridad_maxima.value,
                    "requiere_revision_humana": grupo.requiere_revision_humana,
                }
                for grupo in reporte.indicadores.por_grupo
            ],
        },
        "resultados_dimension": [
            {
                "dimension_codigo": r.dimension_codigo.value,
                "grupo_tematico": r.grupo_tematico,
                "nivel_consolidado": r.nivel_consolidado.value,
                "valor_auxiliar": r.valor_auxiliar,
                "prioridad_documental": r.prioridad_documental.value,
                "justificacion": r.justificacion,
                "requiere_revision_humana": r.requiere_revision_humana,
                "brechas_principales": list(r.brechas_principales),
                "hallazgos_relacionados": [str(h) for h in r.hallazgos_relacionados],
            }
            for r in reporte.resultados_dimension
        ],
        "hallazgos": [
            {
                "hallazgo_id": str(h.id),
                "guardrail_codigo": h.guardrail_codigo,
                "guardrail_version": h.guardrail_version,
                "familia_guardrail": h.familia_guardrail.value,
                "dimensiones_asociadas": [d.value for d in h.dimensiones_asociadas],
                "criterios_asociados": list(h.criterios_asociados),
                "nivel_preliminar": h.nivel_preliminar.value,
                "valor_auxiliar": 2 if h.nivel_preliminar == NivelCobertura.EXPLICITO else 1 if h.nivel_preliminar == NivelCobertura.PARCIAL else 0,
                "prioridad_documental": h.prioridad_documental.value,
                "justificacion": h.justificacion,
                "justificacion_prioridad": h.justificacion_prioridad,
                "requiere_revision_humana": h.requiere_revision_humana,
                "motivo_revision_humana": h.motivo_revision_humana,
                "evidencias": [
                    {
                        "fragmento_id": str(e.fragmento_id),
                        "identificador_ers": e.identificador_ers,
                        "seccion_origen": e.seccion_origen,
                        "texto": e.texto,
                        "posicion_inicio": e.posicion_inicio,
                        "posicion_fin": e.posicion_fin,
                        "tipo_vinculo": e.tipo_vinculo.value,
                        "relevancia": e.relevancia,
                        "observacion": e.observacion,
                    }
                    for e in h.evidencias
                ],
                "fecha_generacion": h.fecha_generacion.isoformat(),
            }
            for h in reporte.hallazgos
        ],
        "advertencias": list(reporte.advertencias),
    }


def obtener_resultado_documento(
    evaluacion: ResultadoEvaluacionEtica,
    nombre_documento: str,
) -> Dict[str, Any]:
    return serializar_reporte_resultados(
        evaluacion,
        nombre_documento=nombre_documento,
    )


__all__ = [
    "ReporteAnalisis",
    "ResultadoDimension",
    "obtener_resultado_documento",
    "serializar_reporte_resultados",
]
