from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    DimensionEtica,
    EstadoAplicacionGuardrail,
    FamiliaGuardrail,
    HallazgoEvaluacion,
    NivelCobertura,
    PrioridadDocumental,
    ResultadoAplicacionGuardrail,
    ResultadoEvaluacionEtica,
    TipoMejora,
)
from etica_ia_ers.recomendaciones import (
    ResultadosIncompatiblesError,
    generar_alertas_y_recomendaciones,
)
from etica_ia_ers.rubrica_y_agregacion import calcular_cobertura_etica


_CONTENIDO_ESPERADO = {
    DimensionEtica.D01: "proposito",
    DimensionEtica.D02: "actores",
    DimensionEtica.D03: "datos utilizados",
    DimensionEtica.D04: "metricas y umbrales de equidad",
    DimensionEtica.D05: "comunica el uso de IA",
    DimensionEtica.D06: "salidas requieren explicacion",
    DimensionEtica.D07: "decisiones supervisadas",
    DimensionEtica.D08: "respuesta ante fallas",
    DimensionEtica.D09: "versionado y trazabilidad",
    DimensionEtica.D10: "impactos sociales",
}


def _hallazgo(
    dimension: DimensionEtica,
    nivel: NivelCobertura,
    analisis_id,
    prioridad: PrioridadDocumental = PrioridadDocumental.MEDIA,
) -> HallazgoEvaluacion:
    return HallazgoEvaluacion(
        analisis_id=analisis_id,
        guardrail_codigo=f"GR-{dimension.value}-PRUEBA",
        guardrail_version=1,
        familia_guardrail=FamiliaGuardrail.PRESENCIA,
        dimensiones_asociadas=(dimension,),
        criterios_asociados=(f"{dimension.value}-C1",),
        nivel_preliminar=nivel,
        prioridad_documental=prioridad,
        justificacion=f"Brecha documental de {dimension.value}.",
        justificacion_prioridad="Prioridad definida por la regla de prueba.",
        requiere_revision_humana=True,
        motivo_revision_humana="Requiere confirmacion humana.",
        evidencias=(),
        fecha_generacion=datetime.now(timezone.utc),
    )


def _resultado_evaluacion(
    niveles,
    *,
    prioridad: PrioridadDocumental = PrioridadDocumental.MEDIA,
    con_error: bool = False,
) -> ResultadoEvaluacionEtica:
    analisis_id = uuid4()
    aplicaciones = []
    for dimension, nivel in niveles.items():
        hallazgo = _hallazgo(dimension, nivel, analisis_id, prioridad)
        aplicaciones.append(
            ResultadoAplicacionGuardrail(
                guardrail_codigo=hallazgo.guardrail_codigo,
                guardrail_version=1,
                estado=EstadoAplicacionGuardrail.APLICADO,
                motivo="Guardrail aplicado en la prueba.",
                hallazgo=hallazgo,
            )
        )
    if con_error:
        aplicaciones.append(
            ResultadoAplicacionGuardrail(
                guardrail_codigo="GR-ERROR-PRUEBA",
                guardrail_version=1,
                estado=EstadoAplicacionGuardrail.ERROR,
                motivo="Falla sintetica.",
            )
        )
    fecha = datetime.now(timezone.utc)
    return ResultadoEvaluacionEtica(
        analisis_id=analisis_id,
        documento_id=uuid4(),
        fecha_inicio=fecha,
        fecha_fin=fecha,
        aplicaciones=tuple(aplicaciones),
    )


def _generar(niveles, **opciones):
    evaluacion = _resultado_evaluacion(niveles, **opciones)
    cobertura = calcular_cobertura_etica(evaluacion)
    resultado = generar_alertas_y_recomendaciones(evaluacion, cobertura)
    return evaluacion, cobertura, resultado


def prueba_genera_alertas_agrupadas_y_omite_dimension_explicita() -> None:
    _, _, resultado = _generar(
        {
            DimensionEtica.D01: NivelCobertura.AUSENTE,
            DimensionEtica.D02: NivelCobertura.PARCIAL,
            DimensionEtica.D03: NivelCobertura.EXPLICITO,
        }
    )

    assert tuple(alerta.dimension for alerta in resultado.alertas) == (
        DimensionEtica.D01,
        DimensionEtica.D02,
    )
    assert tuple(r.dimension for r in resultado.recomendaciones) == (
        DimensionEtica.D01,
        DimensionEtica.D02,
    )
    assert resultado.recomendaciones[0].tipo_mejora == TipoMejora.INCORPORAR
    assert resultado.recomendaciones[1].tipo_mejora == TipoMejora.PRECISAR


def prueba_genera_como_maximo_diez_alertas_en_orden_documental() -> None:
    niveles = {
        dimension: NivelCobertura.AUSENTE
        for dimension in reversed(tuple(DimensionEtica))
    }

    _, _, resultado = _generar(niveles)

    assert len(resultado.alertas) == 10
    assert tuple(alerta.dimension for alerta in resultado.alertas) == tuple(
        DimensionEtica
    )


@pytest.mark.parametrize("dimension", tuple(DimensionEtica))
def prueba_usa_plantilla_versionada_para_cada_dimension(dimension) -> None:
    _, _, resultado = _generar({dimension: NivelCobertura.AUSENTE})

    recomendacion = resultado.recomendaciones[0]
    assert recomendacion.plantilla_version == f"{dimension.value}-v1"
    assert _CONTENIDO_ESPERADO[dimension] in recomendacion.accion_sugerida
    assert recomendacion.accion_sugerida.startswith("Incorporar en la ERS")
    assert "incumple" not in recomendacion.accion_sugerida.lower()
    assert "certifica" not in recomendacion.accion_sugerida.lower()


def prueba_conserva_prioridad_y_trazabilidad_del_resultado() -> None:
    evaluacion, cobertura, generado = _generar(
        {DimensionEtica.D08: NivelCobertura.PARCIAL},
        prioridad=PrioridadDocumental.ALTA,
    )

    dimension = cobertura.resultados_por_dimension[0]
    alerta = generado.alertas[0]
    recomendacion = generado.recomendaciones[0]
    assert generado.analisis_id == evaluacion.analisis_id
    assert generado.documento_id == evaluacion.documento_id
    assert alerta.resultado_dimension_id == dimension.id
    assert recomendacion.resultado_dimension_id == dimension.id
    assert alerta.hallazgos_relacionados == dimension.hallazgos_relacionados
    assert recomendacion.hallazgos_relacionados == dimension.hallazgos_relacionados
    assert alerta.recomendaciones_asociadas == (recomendacion.id,)
    assert alerta.prioridad_documental == PrioridadDocumental.ALTA
    assert recomendacion.prioridad_documental == PrioridadDocumental.ALTA


def prueba_no_convierte_dimensiones_no_evaluadas_en_alertas() -> None:
    _, _, resultado = _generar(
        {DimensionEtica.D01: NivelCobertura.EXPLICITO},
        con_error=True,
    )

    assert resultado.alertas == ()
    assert resultado.recomendaciones == ()
    assert any("No se consideran ausentes" in a for a in resultado.advertencias)
    assert any("guardrails con error" in a for a in resultado.advertencias)


def prueba_resultado_vacio_conserva_advertencias_sin_generar_alertas() -> None:
    evaluacion = _resultado_evaluacion({})
    cobertura = calcular_cobertura_etica(evaluacion)

    resultado = generar_alertas_y_recomendaciones(evaluacion, cobertura)

    assert resultado.alertas == ()
    assert resultado.recomendaciones == ()
    assert resultado.fecha_generacion.tzinfo == timezone.utc
    assert any("No hay dimensiones evaluadas" in a for a in resultado.advertencias)


def prueba_rechaza_evaluacion_y_cobertura_de_distintos_documentos() -> None:
    evaluacion = _resultado_evaluacion(
        {DimensionEtica.D01: NivelCobertura.AUSENTE}
    )
    cobertura = calcular_cobertura_etica(evaluacion)
    incompatible = replace(cobertura, documento_id=uuid4())

    with pytest.raises(ResultadosIncompatiblesError):
        generar_alertas_y_recomendaciones(evaluacion, incompatible)


def prueba_rechaza_evaluacion_y_cobertura_de_distintos_analisis() -> None:
    evaluacion = _resultado_evaluacion(
        {DimensionEtica.D01: NivelCobertura.AUSENTE}
    )
    cobertura = calcular_cobertura_etica(evaluacion)
    dimension = replace(
        cobertura.resultados_por_dimension[0],
        analisis_id=uuid4(),
    )
    incompatible = replace(
        cobertura,
        analisis_id=dimension.analisis_id,
        resultados_por_dimension=(dimension,),
    )

    with pytest.raises(ResultadosIncompatiblesError):
        generar_alertas_y_recomendaciones(evaluacion, incompatible)


def prueba_rechaza_hallazgo_inexistente_en_resultado_dimension() -> None:
    evaluacion = _resultado_evaluacion(
        {DimensionEtica.D01: NivelCobertura.AUSENTE}
    )
    cobertura = calcular_cobertura_etica(evaluacion)
    dimension_invalida = replace(
        cobertura.resultados_por_dimension[0],
        hallazgos_relacionados=(uuid4(),),
    )
    incompatible = replace(
        cobertura,
        resultados_por_dimension=(dimension_invalida,),
    )

    with pytest.raises(ResultadosIncompatiblesError):
        generar_alertas_y_recomendaciones(evaluacion, incompatible)


def prueba_contratos_y_colecciones_son_inmutables() -> None:
    _, _, resultado = _generar(
        {DimensionEtica.D01: NivelCobertura.PARCIAL}
    )

    with pytest.raises(FrozenInstanceError):
        resultado.alertas = ()
    with pytest.raises(TypeError):
        resultado.alertas[0].brechas[0] = "Otra brecha"
