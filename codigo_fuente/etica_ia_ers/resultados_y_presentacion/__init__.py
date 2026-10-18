"""Resultados, indicadores y presentacion para revision humana."""

from __future__ import annotations

from typing import Any, Dict

from etica_ia_ers.dominio import (
    AlertaDocumental,
    DimensionEtica,
    GrupoTematico,
    NivelCobertura,
    PrioridadDocumental,
    RecomendacionDocumental,
    ResultadoAlertasYRecomendaciones,
    ResultadoCoberturaEtica,
    ResultadoDimensionEtica,
    ResultadoEvaluacionEtica,
    resolver_dominio_aplicacion,
)
from etica_ia_ers.recomendaciones import generar_alertas_y_recomendaciones
from etica_ia_ers.rubrica_y_agregacion import (
    GRUPO_POR_DIMENSION,
    NOMBRES_DIMENSION,
    calcular_cobertura_etica,
)

from .errores import (
    ErrorEscrituraReporte,
    ErrorExportacion,
    FormatoExportacionNoSoportadoError,
    ReporteInvalidoError,
)
from .exportacion import (
    AVISO_ALCANCE,
    DIRECTORIO_SALIDA,
    FormatoExportacion,
    ReporteExportado,
    escribir_reporte,
    exportar_reporte,
    formatos_disponibles,
)


_NOMBRES_GRUPO_TEMATICO = {
    GrupoTematico.CONTEXTO_Y_AFECTADOS: "Contexto y afectados",
    GrupoTematico.DATOS_Y_TRATO_JUSTO: "Datos y trato justo",
    GrupoTematico.COMPRENSION_Y_CONTROL_HUMANO: "Comprensión y control humano",
    GrupoTematico.GOBERNANZA_Y_OPERACION_RESPONSABLE: (
        "Gobernanza y operación responsable"
    ),
}

_UMBRAL_COBERTURA_DESARROLLADA = 0.5

_LECTURAS_GLOBALES = {
    "insuficiente": "Cobertura documental insuficiente",
    "inicial": "Cobertura documental inicial",
    "desarrollada": "Cobertura documental desarrollada",
}


def _resultado_dimension_no_evaluada(
    dimension: DimensionEtica,
) -> Dict[str, Any]:

    return {
        "resultado_dimension_id": None,
        "dimension_codigo": dimension.value,
        "dimension_nombre": NOMBRES_DIMENSION[dimension],
        "grupo_tematico": _NOMBRES_GRUPO_TEMATICO[GRUPO_POR_DIMENSION[dimension]],
        "nivel_consolidado": None,
        "valor_auxiliar": None,
        "prioridad_documental": None,
        "justificacion": (
            "El catalogo de guardrails no produjo hallazgos para esta "
            "dimension en la ejecucion actual."
        ),
        "requiere_revision_humana": True,
        "motivo_revision_humana": (
            "Confirmar si la ausencia de hallazgos refleja una omision "
            "real o una limitacion del catalogo aplicado."
        ),
        "brechas_principales": [],
        "hallazgos_relacionados": [],
        "porcentaje_cobertura_ponderada": None,
        "guardrails_criticos_pendientes": [],
    }


def _lectura_global(
    cobertura: ResultadoCoberturaEtica,
    cantidad_no_evaluadas: int,
    total_hallazgos: int,
) -> str:
    if total_hallazgos == 0:
        return _LECTURAS_GLOBALES["insuficiente"]

    total = len(DimensionEtica)
    cobertura_no_ausente = sum(
        1
        for resultado in cobertura.resultados_por_dimension
        if resultado.nivel_consolidado != NivelCobertura.AUSENTE
    )
    proporcion = cobertura_no_ausente / total
    if proporcion < _UMBRAL_COBERTURA_DESARROLLADA:
        return _LECTURAS_GLOBALES["insuficiente"]
    if proporcion < 1.0 or cantidad_no_evaluadas:
        return _LECTURAS_GLOBALES["inicial"]
    return _LECTURAS_GLOBALES["desarrollada"]


def _resumen_ejecutivo(total_hallazgos: int) -> str:
    if total_hallazgos == 0:
        return (
            "No se observaron hallazgos documentales relevantes para los "
            "guardrails evaluados en esta ejecucion."
        )
    return (
        "Se registraron observaciones documentales para la ERS. El reporte "
        "resume la evidencia disponible y destaca los puntos que requieren "
        "revision humana."
    )


def serializar_reporte_resultados(
    evaluacion: ResultadoEvaluacionEtica,
    nombre_documento: str,
) -> Dict[str, Any]:
    cobertura = calcular_cobertura_etica(evaluacion)
    resultado_recomendaciones = generar_alertas_y_recomendaciones(
        evaluacion,
        cobertura,
    )
    total_hallazgos = cobertura.indicadores_globales.total_hallazgos
    dominio_declarado = evaluacion.metadatos.get("dominio")
    if not isinstance(dominio_declarado, str) or not dominio_declarado.strip():
        dominio_declarado = None
    dominio_aplicacion = resolver_dominio_aplicacion(dominio_declarado)

    resultados_serializados = {
        resultado.dimension: _serializar_resultado_dimension(resultado)
        for resultado in cobertura.resultados_por_dimension
    }
    for dimension in cobertura.dimensiones_no_evaluadas:
        resultados_serializados[dimension] = _resultado_dimension_no_evaluada(
            dimension
        )
    resultados_dimension = [
        resultados_serializados[dimension] for dimension in DimensionEtica
    ]

    return {
        "metadatos": {
            "analisis_id": str(cobertura.analisis_id),
            "documento_id": str(cobertura.documento_id),
            "nombre_documento": nombre_documento,
            "fecha_inicio": evaluacion.fecha_inicio.isoformat(),
            "fecha_fin": evaluacion.fecha_fin.isoformat(),
            "estado": "EVALUADO",
            "dominio_declarado": dominio_declarado,
            "dominio_aplicacion": (
                dominio_aplicacion.value if dominio_aplicacion else None
            ),
        },
        "resumen_ejecutivo": _resumen_ejecutivo(total_hallazgos),
        "lectura_global": _lectura_global(
            cobertura, len(cobertura.dimensiones_no_evaluadas), total_hallazgos
        ),
        "indicadores": _serializar_indicadores(
            cobertura,
            resultado_recomendaciones,
        ),
        "resultados_dimension": resultados_dimension,
        "hallazgos": [
            _serializar_hallazgo(hallazgo) for hallazgo in evaluacion.hallazgos
        ],
        "alertas": [
            _serializar_alerta(alerta)
            for alerta in resultado_recomendaciones.alertas
        ],
        "recomendaciones": [
            _serializar_recomendacion(recomendacion)
            for recomendacion in resultado_recomendaciones.recomendaciones
        ],
        "advertencias": list(resultado_recomendaciones.advertencias),
    }


def _serializar_indicadores(
    cobertura: ResultadoCoberturaEtica,
    resultado_recomendaciones: ResultadoAlertasYRecomendaciones,
) -> Dict[str, Any]:
    globales = cobertura.indicadores_globales
    guardrails = cobertura.indicadores_guardrails
    prioridad = cobertura.indicadores_prioridad
    return {
        "total_dimensiones": len(DimensionEtica),
        "dimensiones_ausentes": globales.dimensiones_ausentes,
        "dimensiones_parciales": globales.dimensiones_parciales,
        "dimensiones_explicitas": globales.dimensiones_explicitas,
        "porcentaje_cobertura_explicita": globales.porcentaje_cobertura_explicita,
        "porcentaje_cobertura_no_ausente": globales.porcentaje_cobertura_no_ausente,
        "porcentaje_cobertura_ponderada": globales.porcentaje_cobertura_ponderada,
        "total_hallazgos": globales.total_hallazgos,
        "total_alertas": len(resultado_recomendaciones.alertas),
        "total_recomendaciones": len(resultado_recomendaciones.recomendaciones),
        "recomendaciones_alta_prioridad": sum(
            recomendacion.prioridad_documental == PrioridadDocumental.ALTA
            for recomendacion in resultado_recomendaciones.recomendaciones
        ),
        "hallazgos_con_revision_humana": globales.hallazgos_con_revision_humana,
        "porcentaje_revision_humana": globales.porcentaje_revision_humana,
        "hallazgos_prioridad_alta": prioridad.hallazgos_prioridad_alta,
        "hallazgos_prioridad_media": prioridad.hallazgos_prioridad_media,
        "hallazgos_prioridad_baja": prioridad.hallazgos_prioridad_baja,
        "dimensiones_prioridad_alta": [
            dimension.value for dimension in prioridad.dimensiones_prioridad_alta
        ],
        "guardrails_aplicados": guardrails.guardrails_aplicados,
        "guardrails_no_aplicables": guardrails.guardrails_no_aplicables,
        "guardrails_con_error": guardrails.guardrails_con_error,
        "familias_guardrail_cubiertas": [
            familia.value for familia in guardrails.familias_guardrail_cubiertas
        ],
        "por_grupo": [
            {
                "grupo_tematico": _NOMBRES_GRUPO_TEMATICO[grupo.grupo_tematico],
                "dimensiones_incluidas": [
                    dimension.value for dimension in grupo.dimensiones_incluidas
                ],
                "ausentes": grupo.ausentes,
                "parciales": grupo.parciales,
                "explicitas": grupo.explicitas,
                "prioridad_maxima": (
                    grupo.prioridad_maxima.value
                    if grupo.prioridad_maxima is not None
                    else PrioridadDocumental.BAJA.value
                ),
                "requiere_revision_humana": grupo.requiere_revision_humana,
            }
            for grupo in cobertura.indicadores_por_grupo
        ],
    }


def _serializar_resultado_dimension(
    resultado: ResultadoDimensionEtica,
) -> Dict[str, Any]:
    return {
        "resultado_dimension_id": str(resultado.id),
        "dimension_codigo": resultado.dimension.value,
        "dimension_nombre": resultado.nombre_dimension,
        "grupo_tematico": _NOMBRES_GRUPO_TEMATICO[resultado.grupo_tematico],
        "nivel_consolidado": resultado.nivel_consolidado.value,
        "valor_auxiliar": resultado.valor_auxiliar,
        "prioridad_documental": resultado.prioridad_documental.value,
        "justificacion": resultado.justificacion,
        "requiere_revision_humana": resultado.requiere_revision_humana,
        "motivo_revision_humana": resultado.motivo_revision_humana,
        "brechas_principales": list(resultado.brechas_principales),
        "hallazgos_relacionados": [
            str(hallazgo_id) for hallazgo_id in resultado.hallazgos_relacionados
        ],
        "porcentaje_cobertura_ponderada": resultado.porcentaje_cobertura_ponderada,
        "guardrails_criticos_pendientes": list(
            resultado.guardrails_criticos_pendientes
        ),
    }


def _serializar_alerta(alerta: AlertaDocumental) -> Dict[str, Any]:
    return {
        "alerta_id": str(alerta.id),
        "analisis_id": str(alerta.analisis_id),
        "documento_id": str(alerta.documento_id),
        "resultado_dimension_id": str(alerta.resultado_dimension_id),
        "dimension_codigo": alerta.dimension.value,
        "nivel_cobertura": alerta.nivel_cobertura.value,
        "prioridad_documental": alerta.prioridad_documental.value,
        "titulo": alerta.titulo,
        "descripcion": alerta.descripcion,
        "brechas": list(alerta.brechas),
        "hallazgos_relacionados": [
            str(hallazgo_id) for hallazgo_id in alerta.hallazgos_relacionados
        ],
        "recomendaciones_asociadas": [
            str(recomendacion_id)
            for recomendacion_id in alerta.recomendaciones_asociadas
        ],
        "requiere_revision_humana": alerta.requiere_revision_humana,
        "motivo_revision_humana": alerta.motivo_revision_humana,
    }


def _serializar_recomendacion(
    recomendacion: RecomendacionDocumental,
) -> Dict[str, Any]:
    return {
        "recomendacion_id": str(recomendacion.id),
        "analisis_id": str(recomendacion.analisis_id),
        "resultado_dimension_id": str(recomendacion.resultado_dimension_id),
        "dimension_codigo": recomendacion.dimension.value,
        "hallazgos_relacionados": [
            str(hallazgo_id)
            for hallazgo_id in recomendacion.hallazgos_relacionados
        ],
        "accion_sugerida": recomendacion.accion_sugerida,
        "fundamento": recomendacion.fundamento,
        "prioridad_documental": recomendacion.prioridad_documental.value,
        "tipo_mejora": recomendacion.tipo_mejora.value,
        "plantilla_version": recomendacion.plantilla_version,
    }


def _serializar_hallazgo(hallazgo: Any) -> Dict[str, Any]:
    valor_auxiliar = {
        NivelCobertura.AUSENTE: 0,
        NivelCobertura.PARCIAL: 1,
        NivelCobertura.EXPLICITO: 2,
    }[hallazgo.nivel_preliminar]
    return {
        "hallazgo_id": str(hallazgo.id),
        "analisis_id": str(hallazgo.analisis_id),
        "guardrail_codigo": hallazgo.guardrail_codigo,
        "guardrail_version": hallazgo.guardrail_version,
        "guardrail_nombre": hallazgo.guardrail_nombre,
        "guardrail_descripcion": hallazgo.guardrail_descripcion,
        "guardrail_dominios": [
            dominio.value for dominio in hallazgo.guardrail_dominios
        ],
        "familia_guardrail": hallazgo.familia_guardrail.value,
        "dimensiones_asociadas": [
            dimension.value for dimension in hallazgo.dimensiones_asociadas
        ],
        "criterios_asociados": list(hallazgo.criterios_asociados),
        "nivel_preliminar": hallazgo.nivel_preliminar.value,
        "valor_auxiliar": valor_auxiliar,
        "prioridad_documental": hallazgo.prioridad_documental.value,
        "peso": hallazgo.peso,
        "justificacion": hallazgo.justificacion,
        "justificacion_prioridad": hallazgo.justificacion_prioridad,
        "requiere_revision_humana": hallazgo.requiere_revision_humana,
        "motivo_revision_humana": hallazgo.motivo_revision_humana,
        "evidencias": [
            {
                "fragmento_id": str(evidencia.fragmento_id),
                "identificador_ers": evidencia.identificador_ers,
                "seccion_origen": evidencia.seccion_origen,
                "texto": evidencia.texto,
                "posicion_inicio": evidencia.posicion_inicio,
                "posicion_fin": evidencia.posicion_fin,
                "tipo_vinculo": evidencia.tipo_vinculo.value,
                "relevancia": evidencia.relevancia,
                "observacion": evidencia.observacion,
                "fragmentos_clave": list(evidencia.fragmentos_clave),
            }
            for evidencia in hallazgo.evidencias
        ],
        "fecha_generacion": hallazgo.fecha_generacion.isoformat(),
    }


def obtener_resultado_documento(
    evaluacion: ResultadoEvaluacionEtica,
    nombre_documento: str,
) -> Dict[str, Any]:
    return serializar_reporte_resultados(
        evaluacion,
        nombre_documento=nombre_documento,
    )


def exportar_reporte_documento(
    evaluacion: ResultadoEvaluacionEtica,
    nombre_documento: str,
    formato: Any = FormatoExportacion.JSON,
) -> ReporteExportado:
    """Serializa el reporte de una evaluacion y lo entrega listo para descargar."""
    return exportar_reporte(
        serializar_reporte_resultados(evaluacion, nombre_documento=nombre_documento),
        formato=formato,
    )


__all__ = [
    "AVISO_ALCANCE",
    "DIRECTORIO_SALIDA",
    "ErrorEscrituraReporte",
    "ErrorExportacion",
    "FormatoExportacion",
    "FormatoExportacionNoSoportadoError",
    "ReporteExportado",
    "ReporteInvalidoError",
    "escribir_reporte",
    "exportar_reporte",
    "exportar_reporte_documento",
    "formatos_disponibles",
    "obtener_resultado_documento",
    "serializar_reporte_resultados",
]
