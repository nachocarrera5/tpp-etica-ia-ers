"""Rubrica e indicadores agregados de cobertura documental."""

from __future__ import annotations

from .calculador import calcular_cobertura_etica
from .errores import (
    ErrorRubricaYAgregacion,
    ResultadoEvaluacionInvalidoError,
)

__all__ = [
    "ErrorRubricaYAgregacion",
    "ResultadoEvaluacionInvalidoError",
    "calcular_cobertura_etica",
]

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Mapping, Tuple, Union
from uuid import UUID

from etica_ia_ers.dominio import (
    DimensionEtica,
    HallazgoEvaluacion,
    NivelCobertura,
    PrioridadDocumental,
    ResultadoEvaluacionEtica,
)

VALOR_AUXILIAR_NIVEL: Dict[NivelCobertura, int] = {
    NivelCobertura.AUSENTE: 0,
    NivelCobertura.PARCIAL: 1,
    NivelCobertura.EXPLICITO: 2,
}

TOTAL_DIMENSIONES = 10

_GRUPO_POR_DIMENSION: Dict[DimensionEtica, str] = {
    DimensionEtica.D01: "Contexto y afectados",
    DimensionEtica.D02: "Contexto y afectados",
    DimensionEtica.D03: "Datos y trato justo",
    DimensionEtica.D04: "Datos y trato justo",
    DimensionEtica.D05: "Comprensión y control humano",
    DimensionEtica.D06: "Comprensión y control humano",
    DimensionEtica.D07: "Comprensión y control humano",
    DimensionEtica.D08: "Gobernanza y operación responsable",
    DimensionEtica.D09: "Gobernanza y operación responsable",
    DimensionEtica.D10: "Gobernanza y operación responsable",
}


@dataclass(frozen=True)
class IndicadoresPorGrupo:
    grupo_tematico: str
    dimensiones_incluidas: Tuple[DimensionEtica, ...]
    ausentes: int = 0
    parciales: int = 0
    explicitas: int = 0
    prioridad_maxima: PrioridadDocumental = PrioridadDocumental.BAJA
    requiere_revision_humana: bool = False


@dataclass(frozen=True)
class IndicadoresGlobales:
    total_dimensiones: int
    dimensiones_ausentes: int
    dimensiones_parciales: int
    dimensiones_explicitas: int
    porcentaje_cobertura_explicita: float
    porcentaje_cobertura_no_ausente: float
    total_hallazgos: int
    hallazgos_con_revision_humana: int
    porcentaje_revision_humana: float
    hallazgos_prioridad_alta: int
    hallazgos_prioridad_media: int
    hallazgos_prioridad_baja: int
    dimensiones_prioridad_alta: Tuple[DimensionEtica, ...]
    por_grupo: Tuple[IndicadoresPorGrupo, ...]


@dataclass(frozen=True)
class ResultadoDimension:
    dimension_codigo: DimensionEtica
    grupo_tematico: str
    nivel_consolidado: NivelCobertura
    valor_auxiliar: int
    prioridad_documental: PrioridadDocumental
    justificacion: str
    requiere_revision_humana: bool
    brechas_principales: Tuple[str, ...]
    hallazgos_relacionados: Tuple[UUID, ...]


@dataclass(frozen=True)
class MetadatosReporteAnalisis:
    analisis_id: UUID
    documento_id: UUID
    nombre_documento: str
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str


@dataclass(frozen=True)
class ReporteAnalisis:
    metadatos: MetadatosReporteAnalisis
    resumen_ejecutivo: str
    lectura_global: str
    indicadores: IndicadoresGlobales
    resultados_dimension: Tuple[ResultadoDimension, ...]
    hallazgos: Tuple[HallazgoEvaluacion, ...]
    advertencias: Tuple[str, ...]


def _prioridad_maxima_hallazgos(hallazgos: Iterable[HallazgoEvaluacion]) -> PrioridadDocumental:
    prioridades = [h.prioridad_documental for h in hallazgos]
    if any(p == PrioridadDocumental.ALTA for p in prioridades):
        return PrioridadDocumental.ALTA
    if any(p == PrioridadDocumental.MEDIA for p in prioridades):
        return PrioridadDocumental.MEDIA
    return PrioridadDocumental.BAJA


def _nivel_consolidado_de_dimension(hallazgos: Iterable[HallazgoEvaluacion]) -> NivelCobertura:
    niveles = {h.nivel_preliminar for h in hallazgos}
    if NivelCobertura.EXPLICITO in niveles:
        return NivelCobertura.EXPLICITO
    if NivelCobertura.PARCIAL in niveles:
        return NivelCobertura.PARCIAL
    return NivelCobertura.AUSENTE


def agregar(resultado_evaluacion: ResultadoEvaluacionEtica) -> ReporteAnalisis:
    todos_los_hallazgos = resultado_evaluacion.hallazgos

    metadatos = MetadatosReporteAnalisis(
        analisis_id = resultado_evaluacion.analisis_id,
        documento_id = resultado_evaluacion.documento_id,
        nombre_documento = "documento",
        fecha_inicio = resultado_evaluacion.fecha_inicio,
        fecha_fin = resultado_evaluacion.fecha_fin,
        estado = "EVALUADO",
    )

    hallazgos_por_dimension: Dict[DimensionEtica, Tuple[HallazgoEvaluacion, ...]] = {
        dimension: tuple()
        for dimension in DimensionEtica
    }
    for hallazgo in todos_los_hallazgos:
        for dimension in hallazgo.dimensiones_asociadas:
            hallazgos_por_dimension.setdefault(dimension, tuple())
            hallazgos_por_dimension[dimension] = hallazgos_por_dimension[dimension] + (hallazgo,)

    resultados_dimension = []
    grupo_indicadores: Dict[str, Dict[str, Any]] = {}
    for dimension in DimensionEtica:
        hallazgos = hallazgos_por_dimension.get(dimension, ())
        nivel = _nivel_consolidado_de_dimension(hallazgos)
        prioridad = _prioridad_maxima_hallazgos(hallazgos) if hallazgos else PrioridadDocumental.BAJA
        grupo = _GRUPO_POR_DIMENSION.get(dimension, "General")
        justificacion = (
            "; ".join(h.justificacion for h in hallazgos)
            if hallazgos
            else "No se encontraron evidencias documentales para esta dimensión."
        )
        resultados_dimension.append(
            ResultadoDimension(
                dimension_codigo = dimension,
                grupo_tematico = grupo,
                nivel_consolidado = nivel,
                valor_auxiliar = VALOR_AUXILIAR_NIVEL[nivel],
                prioridad_documental = prioridad,
                justificacion = justificacion,
                requiere_revision_humana = any(h.requiere_revision_humana for h in hallazgos),
                brechas_principales = tuple(
                    h.justificacion for h in hallazgos
                ) or ("Falta evidencia documental para consolidar este requisito.",),
                hallazgos_relacionados = tuple(h.id for h in hallazgos),
            )
        )

        entry = grupo_indicadores.setdefault(
            grupo,
            {
                "grupo_tematico": grupo,
                "dimensiones_incluidas": [],
                "ausentes": 0,
                "parciales": 0,
                "explicitas": 0,
                "prioridad_maxima": PrioridadDocumental.BAJA,
                "requiere_revision_humana": False,
            },
        )
        entry["dimensiones_incluidas"].append(dimension)
        if nivel == NivelCobertura.AUSENTE:
            entry["ausentes"] += 1
        elif nivel == NivelCobertura.PARCIAL:
            entry["parciales"] += 1
        else:
            entry["explicitas"] += 1
        if prioridad in (PrioridadDocumental.ALTA, PrioridadDocumental.MEDIA):
            entry["prioridad_maxima"] = max(
                [entry["prioridad_maxima"], prioridad],
                key=lambda p: {PrioridadDocumental.BAJA: 0, PrioridadDocumental.MEDIA: 1, PrioridadDocumental.ALTA: 2}[p],
            )
        entry["requiere_revision_humana"] = entry["requiere_revision_humana"] or any(
            h.requiere_revision_humana for h in hallazgos
        )

    indicadores_por_grupo = []
    for grupo in grupo_indicadores.values():
        indicadores_por_grupo.append(
            IndicadoresPorGrupo(
                grupo_tematico = grupo["grupo_tematico"],
                dimensiones_incluidas = tuple(grupo["dimensiones_incluidas"]),
                ausentes = grupo["ausentes"],
                parciales = grupo["parciales"],
                explicitas = grupo["explicitas"],
                prioridad_maxima = grupo["prioridad_maxima"],
                requiere_revision_humana = grupo["requiere_revision_humana"],
            )
        )

    total_hallazgos = len(todos_los_hallazgos)
    hallazgos_revision = sum(1 for h in todos_los_hallazgos if h.requiere_revision_humana)
    explicitas = sum(1 for r in resultados_dimension if r.nivel_consolidado == NivelCobertura.EXPLICITO)
    parciales = sum(1 for r in resultados_dimension if r.nivel_consolidado == NivelCobertura.PARCIAL)
    ausentes = sum(1 for r in resultados_dimension if r.nivel_consolidado == NivelCobertura.AUSENTE)
    dimensiones_prioridad_alta = tuple(
        r.dimension_codigo for r in resultados_dimension if r.prioridad_documental == PrioridadDocumental.ALTA
    )
    indicadores = IndicadoresGlobales(
        total_dimensiones = len(DimensionEtica),
        dimensiones_ausentes = ausentes,
        dimensiones_parciales = parciales,
        dimensiones_explicitas = explicitas,
        porcentaje_cobertura_explicita = (explicitas / len(DimensionEtica)) * 100,
        porcentaje_cobertura_no_ausente = ((len(DimensionEtica) - ausentes) / len(DimensionEtica)) * 100,
        total_hallazgos = total_hallazgos,
        hallazgos_con_revision_humana = hallazgos_revision,
        porcentaje_revision_humana = (hallazgos_revision / total_hallazgos * 100) if total_hallazgos else 0.0,
        hallazgos_prioridad_alta = sum(1 for h in todos_los_hallazgos if h.prioridad_documental == PrioridadDocumental.ALTA),
        hallazgos_prioridad_media = sum(1 for h in todos_los_hallazgos if h.prioridad_documental == PrioridadDocumental.MEDIA),
        hallazgos_prioridad_baja = sum(1 for h in todos_los_hallazgos if h.prioridad_documental == PrioridadDocumental.BAJA),
        dimensiones_prioridad_alta = dimensiones_prioridad_alta,
        por_grupo = tuple(sorted(indicadores_por_grupo, key=lambda g: g.grupo_tematico)),
    )

    # NOTA: puede que haya que modificar estos criterios de la lectura global
    lectura_global = (
        "Cobertura documental insuficiente"
        if total_hallazgos == 0
        else "Cobertura documental inicial"
        if explicitas <= TOTAL_DIMENSIONES/2 or parciales <= TOTAL_DIMENSIONES/2 or (explicitas + parciales) <= TOTAL_DIMENSIONES/2 # si la mayoría de las dimensiones no son explícitas ni parciales
        else "Cobertura documental desarrollada"
    )
    resumen = (
        "Se registraron observaciones documentales para la ERS. El reporte resume la evidencia disponible y destaca los puntos que requieren revisión humana."
        if total_hallazgos
        else "No se observaron hallazgos documentales relevantes para los guardrails evaluados en esta ejecución."
    )
    return ReporteAnalisis(
        metadatos = metadatos,
        resumen_ejecutivo = resumen,
        lectura_global = lectura_global,
        indicadores = indicadores,
        resultados_dimension = tuple(resultados_dimension),
        hallazgos = tuple(todos_los_hallazgos),
        advertencias = tuple(resultado_evaluacion.advertencias),
    )


__all__ = [
    "VALOR_AUXILIAR_NIVEL",
    "IndicadoresGlobales",
    "IndicadoresPorGrupo",
    "MetadatosReporteAnalisis",
    "ReporteAnalisis",
    "ResultadoDimension",
    "agregar",
]
