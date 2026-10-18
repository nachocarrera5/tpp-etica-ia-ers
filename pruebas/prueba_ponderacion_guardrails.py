from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import pytest

from etica_ia_ers.dominio import (
    PESO_POR_PRIORIDAD,
    DefinicionGuardrail,
    DimensionEtica,
    EstadoAplicacionGuardrail,
    EstadoGuardrail,
    FamiliaGuardrail,
    FragmentoClasificado,
    FragmentoDocumental,
    HallazgoEvaluacion,
    NivelCobertura,
    PrioridadDocumental,
    ResultadoAnalisisNLP,
    ResultadoAplicacionGuardrail,
    ResultadoEvaluacionEtica,
    SolicitudEvaluacionEtica,
    TextoNormalizado,
    TipoClasificacionFragmento,
    TipoFragmento,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GUARDRAILS_ACTIVOS,
    GuardrailLexico,
    RepositorioGuardrailsEnMemoria,
    senal,
)
from etica_ia_ers.recomendaciones import generar_alertas_y_recomendaciones
from etica_ia_ers.resultados_y_presentacion import (
    FormatoExportacion,
    exportar_reporte,
    serializar_reporte_resultados,
)
from etica_ia_ers.rubrica_y_agregacion import (
    UMBRAL_EXPLICITO_PONDERADO,
    calcular_cobertura_etica,
)


def _definicion(
    codigo: str = "GR-D01-PRES-PRUEBA",
    *,
    prioridad: PrioridadDocumental = PrioridadDocumental.MEDIA,
    peso: Optional[float] = None,
) -> DefinicionGuardrail:
    return DefinicionGuardrail(
        codigo=codigo,
        nombre=f"Guardrail de prueba {codigo}",
        version=1,
        estado=EstadoGuardrail.ACTIVA,
        familia=FamiliaGuardrail.PRESENCIA,
        dimensiones=(DimensionEtica.D01,),
        descripcion="Guardrail usado exclusivamente por la prueba.",
        criterios=("D01-C1",),
        prioridad_base=prioridad,
        peso=peso,
    )


def _hallazgo(
    analisis_id,
    codigo: str,
    nivel: NivelCobertura,
    prioridad: PrioridadDocumental,
    *,
    dimension: DimensionEtica = DimensionEtica.D01,
) -> HallazgoEvaluacion:
    return HallazgoEvaluacion(
        analisis_id=analisis_id,
        guardrail_codigo=codigo,
        guardrail_version=1,
        familia_guardrail=FamiliaGuardrail.PRESENCIA,
        dimensiones_asociadas=(dimension,),
        criterios_asociados=("C1",),
        nivel_preliminar=nivel,
        prioridad_documental=prioridad,
        justificacion=f"Resultado documental de {codigo}.",
        justificacion_prioridad="Prioridad sintetica.",
        requiere_revision_humana=True,
        motivo_revision_humana="Requiere revision humana.",
        evidencias=(),
        fecha_generacion=datetime.now(timezone.utc),
        guardrail_nombre=f"Guardrail {codigo}",
        peso=PESO_POR_PRIORIDAD[prioridad],
    )


def _evaluacion(analisis_id, *hallazgos) -> ResultadoEvaluacionEtica:
    fecha = datetime.now(timezone.utc)
    return ResultadoEvaluacionEtica(
        analisis_id=analisis_id,
        documento_id=uuid4(),
        fecha_inicio=fecha,
        fecha_fin=fecha,
        aplicaciones=tuple(
            ResultadoAplicacionGuardrail(
                guardrail_codigo=hallazgo.guardrail_codigo,
                guardrail_version=1,
                estado=EstadoAplicacionGuardrail.APLICADO,
                motivo="Guardrail aplicable.",
                hallazgo=hallazgo,
            )
            for hallazgo in hallazgos
        ),
    )


def _resultado_nlp(texto: str) -> ResultadoAnalisisNLP:
    fragmento = FragmentoDocumental(
        secuencia_orden=1,
        tipo_fragmento=TipoFragmento.REQUISITO,
        texto=texto,
        seccion_origen="1. Introduccion",
        identificador_ers="RF-01",
        posicion_inicio=0,
        posicion_fin=len(texto),
    )
    return ResultadoAnalisisNLP(
        texto_normalizado=TextoNormalizado(
            original=texto,
            normalizado=texto,
            pasos_aplicados=[],
        ),
        fragmentos_clasificados=(
            FragmentoClasificado(
                fragmento=fragmento,
                clasificacion=TipoClasificacionFragmento.REQUISITO_FUNCIONAL,
                senales=(),
                justificacion="Clasificacion sintetica.",
            ),
        ),
        anotaciones=(),
    )


def prueba_peso_por_defecto_deriva_de_la_prioridad() -> None:
    assert _definicion(prioridad=PrioridadDocumental.BAJA).peso_efectivo == 1.0
    assert _definicion(prioridad=PrioridadDocumental.MEDIA).peso_efectivo == 2.0
    assert _definicion(prioridad=PrioridadDocumental.ALTA).peso_efectivo == 3.0


def prueba_peso_explicito_reemplaza_al_de_la_prioridad() -> None:
    definicion = _definicion(prioridad=PrioridadDocumental.BAJA, peso=4.5)

    assert definicion.peso_efectivo == 4.5


@pytest.mark.parametrize("peso", [0, -1.0])
def prueba_rechaza_pesos_no_positivos(peso: float) -> None:
    with pytest.raises(ValueError, match="peso"):
        _definicion(peso=peso)


def prueba_hallazgo_rechaza_peso_no_positivo() -> None:
    with pytest.raises(ValueError, match="peso"):
        HallazgoEvaluacion(
            analisis_id=uuid4(),
            guardrail_codigo="GR-D01-PRES-PRUEBA",
            guardrail_version=1,
            familia_guardrail=FamiliaGuardrail.PRESENCIA,
            dimensiones_asociadas=(DimensionEtica.D01,),
            criterios_asociados=("C1",),
            nivel_preliminar=NivelCobertura.AUSENTE,
            prioridad_documental=PrioridadDocumental.MEDIA,
            justificacion="Sin evidencia.",
            justificacion_prioridad="Prioridad sintetica.",
            requiere_revision_humana=False,
            motivo_revision_humana=None,
            evidencias=(),
            fecha_generacion=datetime.now(timezone.utc),
            peso=0,
        )


def prueba_catalogo_activo_tiene_pesos_positivos() -> None:
    for guardrail in GUARDRAILS_ACTIVOS:
        definicion = guardrail.definicion
        assert definicion.peso_efectivo > 0, definicion.codigo


def prueba_motor_traslada_el_peso_efectivo_al_hallazgo() -> None:
    guardrail = GuardrailLexico(
        definicion=_definicion(prioridad=PrioridadDocumental.BAJA, peso=2.5),
        senales_explicitas=(senal("proposito", r"proposito"),),
    )
    solicitud = SolicitudEvaluacionEtica(
        documento_id=uuid4(),
        resultado_nlp=_resultado_nlp("El proposito del sistema es asistir."),
    )

    resultado = MotorEvaluacionEtica(
        RepositorioGuardrailsEnMemoria((guardrail,))
    ).evaluar(solicitud)

    assert resultado.hallazgos[0].peso == 2.5


def prueba_calcula_cobertura_ponderada_por_dimension_y_global() -> None:
    analisis_id = uuid4()
    evaluacion = _evaluacion(
        analisis_id,
        # D01: (3 * 1 + 2 * 0.5) / 5 = 80 %.
        _hallazgo(
            analisis_id,
            "GR-D01-A",
            NivelCobertura.EXPLICITO,
            PrioridadDocumental.ALTA,
        ),
        _hallazgo(
            analisis_id,
            "GR-D01-B",
            NivelCobertura.PARCIAL,
            PrioridadDocumental.MEDIA,
        ),
        # D02: sin evidencia, 0 %.
        _hallazgo(
            analisis_id,
            "GR-D02-A",
            NivelCobertura.AUSENTE,
            PrioridadDocumental.BAJA,
            dimension=DimensionEtica.D02,
        ),
    )

    cobertura = calcular_cobertura_etica(evaluacion)

    d01, d02 = cobertura.resultados_por_dimension
    assert d01.porcentaje_cobertura_ponderada == 80.0
    assert d01.nivel_consolidado == NivelCobertura.PARCIAL
    assert "cobertura ponderada de 80.00%" in d01.justificacion
    assert d02.porcentaje_cobertura_ponderada == 0.0
    assert cobertura.indicadores_globales.porcentaje_cobertura_ponderada == 40.0


def prueba_ponderacion_consolida_explicito_si_solo_quedan_brechas_menores() -> None:
    analisis_id = uuid4()
    evaluacion = _evaluacion(
        analisis_id,
        *(
            _hallazgo(
                analisis_id,
                f"GR-D01-ALTA-{indice}",
                NivelCobertura.EXPLICITO,
                PrioridadDocumental.ALTA,
            )
            for indice in range(3)
        ),
        _hallazgo(
            analisis_id,
            "GR-D01-MEDIA",
            NivelCobertura.EXPLICITO,
            PrioridadDocumental.MEDIA,
        ),
        _hallazgo(
            analisis_id,
            "GR-D01-BAJA",
            NivelCobertura.AUSENTE,
            PrioridadDocumental.BAJA,
        ),
    )

    cobertura = calcular_cobertura_etica(evaluacion)
    dimension = cobertura.resultados_por_dimension[0]

    # (9 + 2) / 12 = 91,67 %, por encima del umbral y sin criticos pendientes.
    assert dimension.porcentaje_cobertura_ponderada == 91.67
    assert dimension.nivel_consolidado == NivelCobertura.EXPLICITO
    assert dimension.guardrails_criticos_pendientes == ()
    # La brecha menor sigue visible aunque la dimension sea EXPLICITO.
    assert dimension.brechas_principales == (
        "Falta evidencia documental sobre: Guardrail GR-D01-BAJA.",
    )
    assert dimension.requiere_revision_humana is True
    alertas = generar_alertas_y_recomendaciones(evaluacion, cobertura)
    assert alertas.alertas == ()


def prueba_guardrail_critico_pendiente_impide_consolidar_explicito() -> None:
    analisis_id = uuid4()
    evaluacion = _evaluacion(
        analisis_id,
        *(
            _hallazgo(
                analisis_id,
                f"GR-D01-MEDIA-{indice}",
                NivelCobertura.EXPLICITO,
                PrioridadDocumental.MEDIA,
            )
            for indice in range(5)
        ),
        _hallazgo(
            analisis_id,
            "GR-D01-CRITICO",
            NivelCobertura.PARCIAL,
            PrioridadDocumental.ALTA,
        ),
    )

    cobertura = calcular_cobertura_etica(evaluacion)
    dimension = cobertura.resultados_por_dimension[0]

    # (10 + 1,5) / 13 = 88,46 % supera el umbral, pero el critico lo bloquea.
    assert dimension.porcentaje_cobertura_ponderada / 100 >= (
        UMBRAL_EXPLICITO_PONDERADO
    )
    assert dimension.nivel_consolidado == NivelCobertura.PARCIAL
    assert dimension.guardrails_criticos_pendientes == ("GR-D01-CRITICO",)
    assert "GR-D01-CRITICO" in dimension.justificacion
    alertas = generar_alertas_y_recomendaciones(evaluacion, cobertura)
    assert [alerta.dimension for alerta in alertas.alertas] == [
        DimensionEtica.D01
    ]


def prueba_cobertura_bajo_el_umbral_se_mantiene_parcial() -> None:
    analisis_id = uuid4()
    evaluacion = _evaluacion(
        analisis_id,
        _hallazgo(
            analisis_id,
            "GR-D01-A",
            NivelCobertura.EXPLICITO,
            PrioridadDocumental.MEDIA,
        ),
        _hallazgo(
            analisis_id,
            "GR-D01-B",
            NivelCobertura.AUSENTE,
            PrioridadDocumental.MEDIA,
        ),
    )

    dimension = calcular_cobertura_etica(evaluacion).resultados_por_dimension[0]

    assert dimension.porcentaje_cobertura_ponderada == 50.0
    assert dimension.nivel_consolidado == NivelCobertura.PARCIAL


def prueba_reporte_serializa_pesos_y_cobertura_ponderada() -> None:
    analisis_id = uuid4()
    evaluacion = _evaluacion(
        analisis_id,
        _hallazgo(
            analisis_id,
            "GR-D01-A",
            NivelCobertura.PARCIAL,
            PrioridadDocumental.ALTA,
        ),
    )

    reporte = serializar_reporte_resultados(evaluacion, "ers.txt")

    assert reporte["hallazgos"][0]["peso"] == 3.0
    assert reporte["indicadores"]["porcentaje_cobertura_ponderada"] == 50.0
    d01, d02 = reporte["resultados_dimension"][:2]
    assert d01["porcentaje_cobertura_ponderada"] == 50.0
    assert d01["guardrails_criticos_pendientes"] == ["GR-D01-A"]
    assert d02["porcentaje_cobertura_ponderada"] is None
    assert d02["guardrails_criticos_pendientes"] == []


@pytest.mark.parametrize(
    "formato",
    [FormatoExportacion.MARKDOWN, FormatoExportacion.HTML],
)
def prueba_exportacion_muestra_ponderacion(formato: FormatoExportacion) -> None:
    analisis_id = uuid4()
    evaluacion = _evaluacion(
        analisis_id,
        _hallazgo(
            analisis_id,
            "GR-D01-A",
            NivelCobertura.PARCIAL,
            PrioridadDocumental.ALTA,
        ),
    )
    reporte = serializar_reporte_resultados(evaluacion, "ers.txt")

    contenido = exportar_reporte(reporte, formato).contenido

    assert "Cobertura ponderada" in contenido
    assert "50%" in contenido
    assert "Guardrails críticos pendientes" in contenido
    assert "Peso en la cobertura ponderada" in contenido
