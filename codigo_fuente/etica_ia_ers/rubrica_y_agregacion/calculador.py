from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Sequence, Tuple

from etica_ia_ers.dominio import (
    DimensionEtica,
    EstadoAplicacionGuardrail,
    FamiliaGuardrail,
    GrupoTematico,
    HallazgoEvaluacion,
    IndicadoresGlobales,
    IndicadoresGrupoTematico,
    IndicadoresGuardrails,
    IndicadoresPrioridad,
    NivelCobertura,
    PrioridadDocumental,
    ResultadoCoberturaEtica,
    ResultadoDimensionEtica,
    ResultadoEvaluacionEtica,
)

from .errores import ResultadoEvaluacionInvalidoError


_NOMBRES_DIMENSION = {
    DimensionEtica.D01: "Proposito y contexto",
    DimensionEtica.D02: "Stakeholders e impacto",
    DimensionEtica.D03: "Datos y privacidad",
    DimensionEtica.D04: "Equidad y prevencion de sesgos",
    DimensionEtica.D05: "Transparencia",
    DimensionEtica.D06: "Explicabilidad e interpretabilidad",
    DimensionEtica.D07: "Supervision humana",
    DimensionEtica.D08: "Robustez, seguridad y fiabilidad",
    DimensionEtica.D09: "Accountability y auditoria",
    DimensionEtica.D10: "Impacto social y ambiental",
}

_DIMENSIONES_POR_GRUPO = {
    GrupoTematico.CONTEXTO_Y_AFECTADOS: (
        DimensionEtica.D01,
        DimensionEtica.D02,
    ),
    GrupoTematico.DATOS_Y_TRATO_JUSTO: (
        DimensionEtica.D03,
        DimensionEtica.D04,
    ),
    GrupoTematico.COMPRENSION_Y_CONTROL_HUMANO: (
        DimensionEtica.D05,
        DimensionEtica.D06,
        DimensionEtica.D07,
    ),
    GrupoTematico.GOBERNANZA_Y_OPERACION_RESPONSABLE: (
        DimensionEtica.D08,
        DimensionEtica.D09,
        DimensionEtica.D10,
    ),
}

_GRUPO_POR_DIMENSION = {
    dimension: grupo
    for grupo, dimensiones in _DIMENSIONES_POR_GRUPO.items()
    for dimension in dimensiones
}

_ORDEN_NIVEL = {
    NivelCobertura.AUSENTE: 0,
    NivelCobertura.PARCIAL: 1,
    NivelCobertura.EXPLICITO: 2,
}

_ORDEN_PRIORIDAD = {
    PrioridadDocumental.BAJA: 0,
    PrioridadDocumental.MEDIA: 1,
    PrioridadDocumental.ALTA: 2,
}


def calcular_cobertura_etica(
    resultado_evaluacion: ResultadoEvaluacionEtica,
) -> ResultadoCoberturaEtica:
    """Consolida cobertura documental sin producir un puntaje etico."""
    hallazgos = resultado_evaluacion.hallazgos
    _validar_trazabilidad(resultado_evaluacion, hallazgos)

    resultados_dimension = _consolidar_dimensiones(
        resultado_evaluacion,
        hallazgos,
    )
    dimensiones_evaluadas = tuple(
        resultado.dimension for resultado in resultados_dimension
    )
    dimensiones_no_evaluadas = tuple(
        dimension
        for dimension in DimensionEtica
        if dimension not in dimensiones_evaluadas
    )

    indicadores_globales = _calcular_indicadores_globales(
        resultados_dimension,
        hallazgos,
    )
    indicadores_por_grupo = _calcular_indicadores_por_grupo(
        resultados_dimension
    )
    indicadores_guardrails = _calcular_indicadores_guardrails(
        resultado_evaluacion
    )
    indicadores_prioridad = _calcular_indicadores_prioridad(
        hallazgos,
        resultados_dimension,
    )
    advertencias = _crear_advertencias(
        resultado_evaluacion,
        dimensiones_no_evaluadas,
        indicadores_guardrails.guardrails_con_error,
        bool(resultados_dimension),
    )

    return ResultadoCoberturaEtica(
        analisis_id=resultado_evaluacion.analisis_id,
        documento_id=resultado_evaluacion.documento_id,
        fecha_generacion=datetime.now(timezone.utc),
        resultados_por_dimension=resultados_dimension,
        indicadores_globales=indicadores_globales,
        indicadores_por_grupo=indicadores_por_grupo,
        indicadores_guardrails=indicadores_guardrails,
        indicadores_prioridad=indicadores_prioridad,
        dimensiones_no_evaluadas=dimensiones_no_evaluadas,
        advertencias=advertencias,
    )


def _validar_trazabilidad(
    resultado_evaluacion: ResultadoEvaluacionEtica,
    hallazgos: Sequence[HallazgoEvaluacion],
) -> None:
    ids_vistos = set()
    for hallazgo in hallazgos:
        if hallazgo.analisis_id != resultado_evaluacion.analisis_id:
            raise ResultadoEvaluacionInvalidoError(
                "Todos los hallazgos deben pertenecer al analisis evaluado."
            )
        if hallazgo.id in ids_vistos:
            raise ResultadoEvaluacionInvalidoError(
                "Un hallazgo no puede aparecer mas de una vez."
            )
        ids_vistos.add(hallazgo.id)


def _consolidar_dimensiones(
    resultado_evaluacion: ResultadoEvaluacionEtica,
    hallazgos: Sequence[HallazgoEvaluacion],
) -> Tuple[ResultadoDimensionEtica, ...]:
    por_dimension: Dict[DimensionEtica, List[HallazgoEvaluacion]] = {
        dimension: [] for dimension in DimensionEtica
    }
    for hallazgo in hallazgos:
        for dimension in hallazgo.dimensiones_asociadas:
            por_dimension[dimension].append(hallazgo)

    resultados = []
    for dimension in DimensionEtica:
        relacionados = por_dimension[dimension]
        if not relacionados:
            continue

        conteo_niveles = Counter(
            hallazgo.nivel_preliminar for hallazgo in relacionados
        )
        nivel = min(
            (hallazgo.nivel_preliminar for hallazgo in relacionados),
            key=_ORDEN_NIVEL.__getitem__,
        )
        prioridad = max(
            (hallazgo.prioridad_documental for hallazgo in relacionados),
            key=_ORDEN_PRIORIDAD.__getitem__,
        )
        requiere_revision = any(
            hallazgo.requiere_revision_humana for hallazgo in relacionados
        )
        motivos_revision = _unicos_en_orden(
            hallazgo.motivo_revision_humana
            for hallazgo in relacionados
            if hallazgo.requiere_revision_humana
            and hallazgo.motivo_revision_humana
        )
        brechas = _unicos_en_orden(
            hallazgo.justificacion
            for hallazgo in relacionados
            if hallazgo.nivel_preliminar != NivelCobertura.EXPLICITO
        )

        resultados.append(
            ResultadoDimensionEtica(
                analisis_id=resultado_evaluacion.analisis_id,
                dimension=dimension,
                nombre_dimension=_NOMBRES_DIMENSION[dimension],
                grupo_tematico=_GRUPO_POR_DIMENSION[dimension],
                nivel_consolidado=nivel,
                prioridad_documental=prioridad,
                justificacion=_justificar_consolidacion(
                    relacionados,
                    conteo_niveles,
                    nivel,
                ),
                hallazgos_relacionados=tuple(
                    hallazgo.id for hallazgo in relacionados
                ),
                brechas_principales=brechas,
                requiere_revision_humana=requiere_revision,
                motivo_revision_humana=(
                    " ".join(motivos_revision) if motivos_revision else None
                ),
            )
        )
    return tuple(resultados)


def _justificar_consolidacion(
    hallazgos: Sequence[HallazgoEvaluacion],
    conteo_niveles: Counter,
    nivel: NivelCobertura,
) -> str:
    return (
        f"Se consolidaron {len(hallazgos)} hallazgos: "
        f"{conteo_niveles[NivelCobertura.AUSENTE]} ausentes, "
        f"{conteo_niveles[NivelCobertura.PARCIAL]} parciales y "
        f"{conteo_niveles[NivelCobertura.EXPLICITO]} explicitos. "
        "Se aplica el nivel mas debil para conservar una lectura "
        f"documental prudente; el resultado es {nivel.value}."
    )


def _calcular_indicadores_globales(
    resultados: Sequence[ResultadoDimensionEtica],
    hallazgos: Sequence[HallazgoEvaluacion],
) -> IndicadoresGlobales:
    total = len(resultados)
    conteos = Counter(resultado.nivel_consolidado for resultado in resultados)
    explicitas = conteos[NivelCobertura.EXPLICITO]
    no_ausentes = explicitas + conteos[NivelCobertura.PARCIAL]
    hallazgos_revision = sum(
        hallazgo.requiere_revision_humana for hallazgo in hallazgos
    )
    return IndicadoresGlobales(
        total_dimensiones=total,
        dimensiones_ausentes=conteos[NivelCobertura.AUSENTE],
        dimensiones_parciales=conteos[NivelCobertura.PARCIAL],
        dimensiones_explicitas=explicitas,
        porcentaje_cobertura_explicita=_porcentaje(explicitas, total),
        porcentaje_cobertura_no_ausente=_porcentaje(no_ausentes, total),
        total_hallazgos=len(hallazgos),
        hallazgos_con_revision_humana=hallazgos_revision,
        porcentaje_revision_humana=_porcentaje(
            hallazgos_revision,
            len(hallazgos),
        ),
    )


def _calcular_indicadores_por_grupo(
    resultados: Sequence[ResultadoDimensionEtica],
) -> Tuple[IndicadoresGrupoTematico, ...]:
    por_dimension = {resultado.dimension: resultado for resultado in resultados}
    indicadores = []
    for grupo, dimensiones in _DIMENSIONES_POR_GRUPO.items():
        resultados_grupo = [
            por_dimension[dimension]
            for dimension in dimensiones
            if dimension in por_dimension
        ]
        conteos = Counter(
            resultado.nivel_consolidado for resultado in resultados_grupo
        )
        prioridad_maxima = (
            max(
                (
                    resultado.prioridad_documental
                    for resultado in resultados_grupo
                ),
                key=_ORDEN_PRIORIDAD.__getitem__,
            )
            if resultados_grupo
            else None
        )
        indicadores.append(
            IndicadoresGrupoTematico(
                grupo_tematico=grupo,
                dimensiones_incluidas=dimensiones,
                dimensiones_evaluadas=tuple(
                    resultado.dimension for resultado in resultados_grupo
                ),
                ausentes=conteos[NivelCobertura.AUSENTE],
                parciales=conteos[NivelCobertura.PARCIAL],
                explicitas=conteos[NivelCobertura.EXPLICITO],
                prioridad_maxima=prioridad_maxima,
                requiere_revision_humana=any(
                    resultado.requiere_revision_humana
                    for resultado in resultados_grupo
                ),
                brechas_principales=_unicos_en_orden(
                    brecha
                    for resultado in resultados_grupo
                    for brecha in resultado.brechas_principales
                ),
            )
        )
    return tuple(indicadores)


def _calcular_indicadores_guardrails(
    resultado: ResultadoEvaluacionEtica,
) -> IndicadoresGuardrails:
    estados = Counter(aplicacion.estado for aplicacion in resultado.aplicaciones)
    familias = Counter(
        hallazgo.familia_guardrail for hallazgo in resultado.hallazgos
    )
    familias_cubiertas = tuple(
        familia for familia in FamiliaGuardrail if familias[familia]
    )
    return IndicadoresGuardrails(
        total_guardrails=len(resultado.aplicaciones),
        guardrails_aplicados=estados[EstadoAplicacionGuardrail.APLICADO],
        guardrails_no_aplicables=estados[
            EstadoAplicacionGuardrail.NO_APLICABLE
        ],
        guardrails_con_error=estados[EstadoAplicacionGuardrail.ERROR],
        familias_guardrail_cubiertas=familias_cubiertas,
        hallazgos_por_familia={
            familia: familias[familia] for familia in familias_cubiertas
        },
    )


def _calcular_indicadores_prioridad(
    hallazgos: Sequence[HallazgoEvaluacion],
    resultados: Sequence[ResultadoDimensionEtica],
) -> IndicadoresPrioridad:
    prioridades = Counter(
        hallazgo.prioridad_documental for hallazgo in hallazgos
    )
    return IndicadoresPrioridad(
        hallazgos_prioridad_alta=prioridades[PrioridadDocumental.ALTA],
        hallazgos_prioridad_media=prioridades[PrioridadDocumental.MEDIA],
        hallazgos_prioridad_baja=prioridades[PrioridadDocumental.BAJA],
        dimensiones_prioridad_alta=tuple(
            resultado.dimension
            for resultado in resultados
            if resultado.prioridad_documental == PrioridadDocumental.ALTA
        ),
    )


def _crear_advertencias(
    resultado: ResultadoEvaluacionEtica,
    dimensiones_no_evaluadas: Tuple[DimensionEtica, ...],
    cantidad_errores: int,
    tiene_dimensiones: bool,
) -> Tuple[str, ...]:
    advertencias: List[str] = list(resultado.advertencias)
    if dimensiones_no_evaluadas:
        codigos = ", ".join(
            dimension.value for dimension in dimensiones_no_evaluadas
        )
        advertencias.append(
            "El catalogo no produjo hallazgos para las dimensiones: "
            f"{codigos}. No se consideran ausentes."
        )
    if cantidad_errores:
        advertencias.append(
            f"La evaluacion contiene {cantidad_errores} guardrails con error; "
            "los indicadores deben interpretarse con esa limitacion."
        )
    if not tiene_dimensiones:
        advertencias.append(
            "No hay dimensiones evaluadas; los porcentajes de cobertura son 0."
        )
    return _unicos_en_orden(advertencias)


def _porcentaje(cantidad: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(cantidad * 100 / total, 2)


def _unicos_en_orden(valores: Iterable[str]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(valores))
