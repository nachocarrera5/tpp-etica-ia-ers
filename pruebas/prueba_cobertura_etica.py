from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    ContextoEvaluacionEtica,
    DecisionAplicabilidad,
    DefinicionGuardrail,
    DimensionEtica,
    EstadoAplicacionGuardrail,
    EstadoGuardrail,
    EvaluacionPreliminarGuardrail,
    FamiliaGuardrail,
    GrupoTematico,
    HallazgoEvaluacion,
    NivelCobertura,
    PrioridadDocumental,
    ResultadoAnalisisNLP,
    ResultadoAplicacionGuardrail,
    ResultadoEvaluacionEtica,
    SolicitudEvaluacionEtica,
    TextoNormalizado,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.rubrica_y_agregacion import (
    ResultadoEvaluacionInvalidoError,
    calcular_cobertura_etica,
)


def _hallazgo(
    codigo: str,
    dimensiones: Tuple[DimensionEtica, ...],
    nivel: NivelCobertura,
    *,
    prioridad: PrioridadDocumental = PrioridadDocumental.MEDIA,
    familia: FamiliaGuardrail = FamiliaGuardrail.PRESENCIA,
    analisis_id=None,
    revision: bool = False,
    justificacion: Optional[str] = None,
) -> HallazgoEvaluacion:
    return HallazgoEvaluacion(
        analisis_id=analisis_id or uuid4(),
        guardrail_codigo=codigo,
        guardrail_version=1,
        familia_guardrail=familia,
        dimensiones_asociadas=dimensiones,
        criterios_asociados=("C1",),
        nivel_preliminar=nivel,
        prioridad_documental=prioridad,
        justificacion=justificacion or f"Resultado documental de {codigo}.",
        justificacion_prioridad="Prioridad sintetica.",
        requiere_revision_humana=revision,
        motivo_revision_humana=(
            "Requiere interpretacion experta." if revision else None
        ),
        evidencias=(),
        fecha_generacion=datetime.now(timezone.utc),
    )


def _aplicacion(hallazgo: HallazgoEvaluacion) -> ResultadoAplicacionGuardrail:
    return ResultadoAplicacionGuardrail(
        guardrail_codigo=hallazgo.guardrail_codigo,
        guardrail_version=hallazgo.guardrail_version,
        estado=EstadoAplicacionGuardrail.APLICADO,
        motivo="Guardrail aplicable.",
        hallazgo=hallazgo,
    )


def _sin_hallazgo(
    codigo: str,
    estado: EstadoAplicacionGuardrail,
) -> ResultadoAplicacionGuardrail:
    return ResultadoAplicacionGuardrail(
        guardrail_codigo=codigo,
        guardrail_version=1,
        estado=estado,
        motivo="Resultado sintetico sin hallazgo.",
    )


def _resultado(*aplicaciones, analisis_id=None, advertencias=()):
    analisis_id = analisis_id or uuid4()
    aplicaciones_ajustadas = []
    for aplicacion in aplicaciones:
        hallazgo = aplicacion.hallazgo
        if hallazgo is not None and hallazgo.analisis_id != analisis_id:
            hallazgo = _hallazgo(
                hallazgo.guardrail_codigo,
                hallazgo.dimensiones_asociadas,
                hallazgo.nivel_preliminar,
                prioridad=hallazgo.prioridad_documental,
                familia=hallazgo.familia_guardrail,
                analisis_id=analisis_id,
                revision=hallazgo.requiere_revision_humana,
                justificacion=hallazgo.justificacion,
            )
            aplicacion = _aplicacion(hallazgo)
        aplicaciones_ajustadas.append(aplicacion)
    fecha = datetime.now(timezone.utc)
    return ResultadoEvaluacionEtica(
        analisis_id=analisis_id,
        documento_id=uuid4(),
        fecha_inicio=fecha,
        fecha_fin=fecha,
        aplicaciones=tuple(aplicaciones_ajustadas),
        advertencias=advertencias,
    )


def prueba_consolida_cobertura_incompleta_y_prioridad_maxima() -> None:
    analisis_id = uuid4()
    explicito = _hallazgo(
        "GR-EXP",
        (DimensionEtica.D01,),
        NivelCobertura.EXPLICITO,
        prioridad=PrioridadDocumental.BAJA,
        analisis_id=analisis_id,
    )
    parcial = _hallazgo(
        "GR-PAR",
        (DimensionEtica.D01,),
        NivelCobertura.PARCIAL,
        prioridad=PrioridadDocumental.ALTA,
        analisis_id=analisis_id,
        revision=True,
        justificacion="Falta delimitar el alcance.",
    )
    resultado = _resultado(
        _aplicacion(explicito),
        _aplicacion(parcial),
        analisis_id=analisis_id,
    )

    cobertura = calcular_cobertura_etica(resultado)

    dimension = cobertura.resultados_por_dimension[0]
    assert dimension.nivel_consolidado == NivelCobertura.PARCIAL
    assert dimension.valor_auxiliar == 1
    assert dimension.prioridad_documental == PrioridadDocumental.ALTA
    assert dimension.requiere_revision_humana is True
    assert dimension.motivo_revision_humana == "Requiere interpretacion experta."
    assert dimension.hallazgos_relacionados == (explicito.id, parcial.id)
    assert dimension.brechas_principales == ("Falta delimitar el alcance.",)
    assert "combina evidencia con brechas" in dimension.justificacion


def prueba_dimension_con_evidencia_y_ausencias_es_parcial() -> None:
    analisis_id = uuid4()
    explicito = _hallazgo(
        "GR-EXP",
        (DimensionEtica.D01,),
        NivelCobertura.EXPLICITO,
        analisis_id=analisis_id,
    )
    ausente = _hallazgo(
        "GR-AUS",
        (DimensionEtica.D01,),
        NivelCobertura.AUSENTE,
        analisis_id=analisis_id,
    )

    cobertura = calcular_cobertura_etica(
        _resultado(
            _aplicacion(explicito),
            _aplicacion(ausente),
            analisis_id=analisis_id,
        )
    )

    assert (
        cobertura.resultados_por_dimension[0].nivel_consolidado
        == NivelCobertura.PARCIAL
    )


def prueba_dimension_sin_evidencia_es_ausente() -> None:
    ausente = _hallazgo(
        "GR-AUS",
        (DimensionEtica.D01,),
        NivelCobertura.AUSENTE,
    )

    cobertura = calcular_cobertura_etica(_resultado(_aplicacion(ausente)))

    assert (
        cobertura.resultados_por_dimension[0].nivel_consolidado
        == NivelCobertura.AUSENTE
    )


def prueba_hallazgo_multidimensional_conserva_orden_y_porcentajes() -> None:
    analisis_id = uuid4()
    multidimensional = _hallazgo(
        "GR-MULTI",
        (DimensionEtica.D02, DimensionEtica.D01),
        NivelCobertura.EXPLICITO,
        analisis_id=analisis_id,
    )
    parcial = _hallazgo(
        "GR-D03",
        (DimensionEtica.D03,),
        NivelCobertura.PARCIAL,
        analisis_id=analisis_id,
    )

    cobertura = calcular_cobertura_etica(
        _resultado(
            _aplicacion(multidimensional),
            _aplicacion(parcial),
            analisis_id=analisis_id,
        )
    )

    assert tuple(
        resultado.dimension for resultado in cobertura.resultados_por_dimension
    ) == (DimensionEtica.D01, DimensionEtica.D02, DimensionEtica.D03)
    assert cobertura.resultados_por_dimension[0].hallazgos_relacionados == (
        multidimensional.id,
    )
    globales = cobertura.indicadores_globales
    assert globales.total_dimensiones == 3
    assert globales.dimensiones_parciales == 1
    assert globales.dimensiones_explicitas == 2
    assert globales.porcentaje_cobertura_explicita == 66.67
    assert globales.porcentaje_cobertura_no_ausente == 100.0
    assert globales.total_hallazgos == 2
    assert globales.hallazgos_con_revision_humana == 0
    assert globales.porcentaje_revision_humana == 0.0


def prueba_calcula_indicadores_por_grupo_guardrail_y_prioridad() -> None:
    analisis_id = uuid4()
    ausente = _hallazgo(
        "GR-D01",
        (DimensionEtica.D01,),
        NivelCobertura.AUSENTE,
        prioridad=PrioridadDocumental.ALTA,
        familia=FamiliaGuardrail.DELIMITACION,
        analisis_id=analisis_id,
        revision=True,
    )
    explicito = _hallazgo(
        "GR-D03",
        (DimensionEtica.D03,),
        NivelCobertura.EXPLICITO,
        prioridad=PrioridadDocumental.BAJA,
        familia=FamiliaGuardrail.VERIFICABILIDAD,
        analisis_id=analisis_id,
    )
    resultado = _resultado(
        _aplicacion(ausente),
        _sin_hallazgo("GR-NA", EstadoAplicacionGuardrail.NO_APLICABLE),
        _sin_hallazgo("GR-ERROR", EstadoAplicacionGuardrail.ERROR),
        _aplicacion(explicito),
        analisis_id=analisis_id,
    )

    cobertura = calcular_cobertura_etica(resultado)

    guardrails = cobertura.indicadores_guardrails
    assert guardrails.total_guardrails == 4
    assert guardrails.guardrails_aplicados == 2
    assert guardrails.guardrails_no_aplicables == 1
    assert guardrails.guardrails_con_error == 1
    assert guardrails.familias_guardrail_cubiertas == (
        FamiliaGuardrail.DELIMITACION,
        FamiliaGuardrail.VERIFICABILIDAD,
    )
    assert guardrails.hallazgos_por_familia == {
        FamiliaGuardrail.DELIMITACION: 1,
        FamiliaGuardrail.VERIFICABILIDAD: 1,
    }

    contexto = cobertura.indicadores_por_grupo[0]
    datos = cobertura.indicadores_por_grupo[1]
    assert contexto.grupo_tematico == GrupoTematico.CONTEXTO_Y_AFECTADOS
    assert contexto.dimensiones_evaluadas == (DimensionEtica.D01,)
    assert contexto.ausentes == 1
    assert contexto.prioridad_maxima == PrioridadDocumental.ALTA
    assert contexto.requiere_revision_humana is True
    assert contexto.brechas_principales == (
        "Resultado documental de GR-D01.",
    )
    assert datos.dimensiones_evaluadas == (DimensionEtica.D03,)
    assert datos.explicitas == 1

    prioridades = cobertura.indicadores_prioridad
    assert prioridades.hallazgos_prioridad_alta == 1
    assert prioridades.hallazgos_prioridad_baja == 1
    assert prioridades.dimensiones_prioridad_alta == (DimensionEtica.D01,)
    assert any(
        "1 guardrails con error" in advertencia
        for advertencia in cobertura.advertencias
    )


def prueba_catalogo_parcial_no_convierte_dimensiones_en_ausentes() -> None:
    resultado = _resultado(
        _aplicacion(
            _hallazgo(
                "GR-D01",
                (DimensionEtica.D01,),
                NivelCobertura.EXPLICITO,
            )
        ),
        advertencias=("Advertencia previa.",),
    )

    cobertura = calcular_cobertura_etica(resultado)

    assert cobertura.indicadores_globales.total_dimensiones == 1
    assert cobertura.indicadores_globales.dimensiones_ausentes == 0
    assert cobertura.dimensiones_no_evaluadas == tuple(DimensionEtica)[1:]
    assert cobertura.advertencias[0] == "Advertencia previa."
    assert "No se consideran ausentes" in cobertura.advertencias[1]


def prueba_resultado_vacio_devuelve_porcentajes_cero_y_advertencia() -> None:
    cobertura = calcular_cobertura_etica(_resultado())

    assert cobertura.resultados_por_dimension == ()
    assert cobertura.indicadores_globales.total_dimensiones == 0
    assert cobertura.indicadores_globales.porcentaje_cobertura_explicita == 0.0
    assert cobertura.indicadores_globales.porcentaje_cobertura_no_ausente == 0.0
    assert cobertura.indicadores_globales.porcentaje_revision_humana == 0.0
    assert cobertura.dimensiones_no_evaluadas == tuple(DimensionEtica)
    assert any(
        "No hay dimensiones evaluadas" in advertencia
        for advertencia in cobertura.advertencias
    )


def prueba_rechaza_hallazgo_de_otro_analisis() -> None:
    hallazgo = _hallazgo(
        "GR-INVALIDO",
        (DimensionEtica.D01,),
        NivelCobertura.AUSENTE,
    )
    fecha = datetime.now(timezone.utc)
    resultado = ResultadoEvaluacionEtica(
        analisis_id=uuid4(),
        documento_id=uuid4(),
        fecha_inicio=fecha,
        fecha_fin=fecha,
        aplicaciones=(_aplicacion(hallazgo),),
    )

    with pytest.raises(ResultadoEvaluacionInvalidoError):
        calcular_cobertura_etica(resultado)


def prueba_contratos_y_colecciones_son_inmutables() -> None:
    cobertura = calcular_cobertura_etica(
        _resultado(
            _aplicacion(
                _hallazgo(
                    "GR-INMUTABLE",
                    (DimensionEtica.D01,),
                    NivelCobertura.AUSENTE,
                )
            )
        )
    )

    with pytest.raises(FrozenInstanceError):
        cobertura.advertencias = ()
    with pytest.raises(TypeError):
        cobertura.indicadores_guardrails.hallazgos_por_familia[
            FamiliaGuardrail.PRESENCIA
        ] = 99


@dataclass(frozen=True)
class _GuardrailSintetico:
    definicion: DefinicionGuardrail

    def decidir_aplicabilidad(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> DecisionAplicabilidad:
        return DecisionAplicabilidad(True, "Aplica a la prueba integral.")

    def evaluar(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> EvaluacionPreliminarGuardrail:
        return EvaluacionPreliminarGuardrail(
            nivel=NivelCobertura.AUSENTE,
            justificacion="No se encontro evidencia sintetica.",
            prioridad=PrioridadDocumental.MEDIA,
            justificacion_prioridad="Prioridad sintetica.",
        )


def prueba_integra_motor_con_guardrails_sinteticos_d01_d10() -> None:
    guardrails = tuple(
        _GuardrailSintetico(
            DefinicionGuardrail(
                codigo=f"GR-{dimension.value}-PRUEBA",
                nombre=f"Prueba {dimension.value}",
                version=1,
                estado=EstadoGuardrail.ACTIVA,
                familia=FamiliaGuardrail.PRESENCIA,
                dimensiones=(dimension,),
                descripcion="Guardrail sintetico de integracion.",
            )
        )
        for dimension in DimensionEtica
    )
    resultado_nlp = ResultadoAnalisisNLP(
        texto_normalizado=TextoNormalizado(
            original="ERS sintetica.",
            normalizado="ERS sintetica.",
            pasos_aplicados=(),
        ),
        fragmentos_clasificados=(),
        anotaciones=(),
    )
    resultado_motor = MotorEvaluacionEtica(
        RepositorioGuardrailsEnMemoria(guardrails)
    ).evaluar(
        SolicitudEvaluacionEtica(
            documento_id=uuid4(),
            resultado_nlp=resultado_nlp,
        )
    )

    cobertura = calcular_cobertura_etica(resultado_motor)

    assert cobertura.analisis_id == resultado_motor.analisis_id
    assert cobertura.documento_id == resultado_motor.documento_id
    assert cobertura.fecha_generacion.tzinfo == timezone.utc
    assert cobertura.indicadores_globales.total_dimensiones == 10
    assert cobertura.indicadores_globales.dimensiones_ausentes == 10
    assert cobertura.dimensiones_no_evaluadas == ()
    assert cobertura.indicadores_guardrails.guardrails_aplicados == 10
    assert len(cobertura.indicadores_por_grupo) == 4
