from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from typing import Optional
from uuid import UUID, uuid4

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
    FragmentoClasificado,
    FragmentoDocumental,
    NivelCobertura,
    PrioridadDocumental,
    ReferenciaEvidencia,
    ResultadoAnalisisNLP,
    SolicitudEvaluacionEtica,
    TextoNormalizado,
    TipoClasificacionFragmento,
    TipoFragmento,
    TipoVinculoEvidencia,
)
from etica_ia_ers.evaluacion_documental import MotorEvaluacionEtica
from etica_ia_ers.modelo_etico_y_guardrails import (
    GuardrailDuplicadoError,
    RepositorioGuardrailsEnMemoria,
)
from etica_ia_ers.procesamiento_textual_y_nlp import analizar_texto


@dataclass(frozen=True)
class GuardrailSintetico:
    definicion: DefinicionGuardrail
    decision: DecisionAplicabilidad
    resultado: Optional[EvaluacionPreliminarGuardrail] = None
    error_al_evaluar: Optional[Exception] = None
    metadato_requerido: Optional[str] = None

    def decidir_aplicabilidad(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> DecisionAplicabilidad:
        if self.metadato_requerido is not None:
            aplica = bool(contexto.metadatos.get(self.metadato_requerido))
            return DecisionAplicabilidad(
                aplica=aplica,
                motivo="El contexto contiene el metadato requerido."
                if aplica
                else "El contexto no contiene el metadato requerido.",
            )
        return self.decision

    def evaluar(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> EvaluacionPreliminarGuardrail:
        if self.error_al_evaluar is not None:
            raise self.error_al_evaluar
        assert contexto.analisis_id
        assert self.resultado is not None
        return self.resultado


def _definicion(
    codigo: str,
    *,
    version: int = 1,
    estado: EstadoGuardrail = EstadoGuardrail.ACTIVA,
    revision: bool = False,
) -> DefinicionGuardrail:
    return DefinicionGuardrail(
        codigo=codigo,
        nombre=f"Guardrail sintetico {codigo}",
        version=version,
        estado=estado,
        familia=FamiliaGuardrail.PRESENCIA,
        dimensiones=(DimensionEtica.D01, DimensionEtica.D03),
        descripcion="Guardrail usado exclusivamente por la prueba.",
        criterios=("criterio-1", "criterio-2"),
        prioridad_base=PrioridadDocumental.ALTA,
        requiere_revision_por_defecto=revision,
    )


def _fragmento(texto: str = "El sistema deberá registrar cada decisión."):
    return FragmentoDocumental(
        secuencia_orden=1,
        tipo_fragmento=TipoFragmento.REQUISITO,
        texto=texto,
        seccion_origen="2. Requisitos funcionales",
        identificador_ers="RF-01",
        posicion_inicio=0,
        posicion_fin=len(texto),
    )


def _resultado_nlp(fragmento=None) -> ResultadoAnalisisNLP:
    fragmento = fragmento or _fragmento()
    return ResultadoAnalisisNLP(
        texto_normalizado=TextoNormalizado(
            original=fragmento.texto,
            normalizado=fragmento.texto,
            pasos_aplicados=[],
        ),
        fragmentos_clasificados=(
            FragmentoClasificado(
                fragmento=fragmento,
                clasificacion=TipoClasificacionFragmento.REQUISITO_FUNCIONAL,
                senales=("comportamiento requerido",),
                justificacion="Clasificacion sintetica.",
            ),
        ),
        anotaciones=(),
    )


def _evaluacion(
    nivel: NivelCobertura,
    *evidencias: ReferenciaEvidencia,
    prioridad: PrioridadDocumental = PrioridadDocumental.MEDIA,
    revision: bool = False,
) -> EvaluacionPreliminarGuardrail:
    return EvaluacionPreliminarGuardrail(
        nivel=nivel,
        justificacion="Justificacion documental legible.",
        prioridad=prioridad,
        justificacion_prioridad="Prioridad asignada por la regla.",
        evidencias=tuple(evidencias),
        requiere_revision_humana=revision,
        motivo_revision_humana="Requiere criterio experto." if revision else None,
    )


def _guardrail(
    codigo: str,
    resultado: Optional[EvaluacionPreliminarGuardrail],
    *,
    aplica: bool = True,
    estado: EstadoGuardrail = EstadoGuardrail.ACTIVA,
    error: Optional[Exception] = None,
    revision: bool = False,
) -> GuardrailSintetico:
    return GuardrailSintetico(
        definicion=_definicion(codigo, estado=estado, revision=revision),
        decision=DecisionAplicabilidad(
            aplica=aplica,
            motivo="Aplica al documento." if aplica else "Fuera de alcance.",
        ),
        resultado=resultado,
        error_al_evaluar=error,
    )


def _evaluar(resultado_nlp, *guardrails, metadatos=None):
    documento_id = uuid4()
    motor = MotorEvaluacionEtica(
        RepositorioGuardrailsEnMemoria(guardrails)
    )
    resultado = motor.evaluar(
        SolicitudEvaluacionEtica(
            documento_id=documento_id,
            resultado_nlp=resultado_nlp,
            metadatos=metadatos or {},
        )
    )
    return documento_id, resultado


def prueba_aplica_guardrail_y_materializa_evidencia_trazable() -> None:
    fragmento = _fragmento()
    referencia = ReferenciaEvidencia(
        fragmento_id=fragmento.id,
        tipo_vinculo=TipoVinculoEvidencia.SOPORTA,
        relevancia=0.9,
        observacion="La evidencia es directa.",
    )
    guardrail = _guardrail(
        "GR-PRUEBA-01",
        _evaluacion(NivelCobertura.EXPLICITO, referencia),
    )

    documento_id, resultado = _evaluar(_resultado_nlp(fragmento), guardrail)

    aplicacion = resultado.aplicaciones[0]
    hallazgo = aplicacion.hallazgo
    assert resultado.documento_id == documento_id
    assert aplicacion.estado == EstadoAplicacionGuardrail.APLICADO
    assert hallazgo is not None
    assert hallazgo.analisis_id == resultado.analisis_id
    assert hallazgo.guardrail_codigo == guardrail.definicion.codigo
    assert hallazgo.guardrail_version == guardrail.definicion.version
    assert hallazgo.familia_guardrail == FamiliaGuardrail.PRESENCIA
    assert hallazgo.dimensiones_asociadas == (
        DimensionEtica.D01,
        DimensionEtica.D03,
    )
    assert hallazgo.criterios_asociados == ("criterio-1", "criterio-2")
    assert hallazgo.nivel_preliminar == NivelCobertura.EXPLICITO
    assert hallazgo.evidencias[0].fragmento_id == fragmento.id
    assert hallazgo.evidencias[0].texto == fragmento.texto
    assert hallazgo.evidencias[0].seccion_origen == fragmento.seccion_origen
    assert hallazgo.evidencias[0].identificador_ers == "RF-01"
    assert hallazgo.evidencias[0].posicion_inicio == fragmento.posicion_inicio
    assert hallazgo.evidencias[0].posicion_fin == fragmento.posicion_fin


@pytest.mark.parametrize(
    ("nivel", "vinculo"),
    [
        (NivelCobertura.AUSENTE, None),
        (NivelCobertura.PARCIAL, TipoVinculoEvidencia.CONTEXTUALIZA),
    ],
)
def prueba_admite_ausencia_sin_evidencia_y_parcial_contextual(
    nivel: NivelCobertura,
    vinculo: Optional[TipoVinculoEvidencia],
) -> None:
    fragmento = _fragmento()
    evidencias = (
        ()
        if vinculo is None
        else (ReferenciaEvidencia(fragmento.id, vinculo),)
    )
    guardrail = _guardrail("GR-PRUEBA-02", _evaluacion(nivel, *evidencias))

    _, resultado = _evaluar(_resultado_nlp(fragmento), guardrail)

    hallazgo = resultado.hallazgos[0]
    assert hallazgo.nivel_preliminar == nivel
    assert len(hallazgo.evidencias) == len(evidencias)


def prueba_guardrail_no_aplicable_no_genera_hallazgo() -> None:
    guardrail = _guardrail("GR-PRUEBA-03", None, aplica=False)

    _, resultado = _evaluar(_resultado_nlp(), guardrail)

    assert resultado.aplicaciones[0].estado == (
        EstadoAplicacionGuardrail.NO_APLICABLE
    )
    assert resultado.aplicaciones[0].hallazgo is None
    assert resultado.hallazgos == ()


def prueba_error_de_una_regla_no_interrumpe_las_siguientes() -> None:
    primero = _guardrail(
        "GR-PRUEBA-04",
        None,
        error=RuntimeError("fallo controlado"),
    )
    segundo = _guardrail(
        "GR-PRUEBA-05",
        _evaluacion(NivelCobertura.AUSENTE),
    )

    _, resultado = _evaluar(_resultado_nlp(), primero, segundo)

    assert [aplicacion.guardrail_codigo for aplicacion in resultado.aplicaciones] == [
        "GR-PRUEBA-04",
        "GR-PRUEBA-05",
    ]
    assert [aplicacion.estado for aplicacion in resultado.aplicaciones] == [
        EstadoAplicacionGuardrail.ERROR,
        EstadoAplicacionGuardrail.APLICADO,
    ]
    assert "fallo controlado" in resultado.aplicaciones[0].motivo


def prueba_rechaza_evidencia_de_fragmento_inexistente_sin_detener_motor() -> None:
    referencia = ReferenciaEvidencia(
        fragmento_id=uuid4(),
        tipo_vinculo=TipoVinculoEvidencia.SOPORTA,
    )
    invalido = _guardrail(
        "GR-PRUEBA-06",
        _evaluacion(NivelCobertura.EXPLICITO, referencia),
    )
    valido = _guardrail(
        "GR-PRUEBA-07",
        _evaluacion(NivelCobertura.AUSENTE),
    )

    _, resultado = _evaluar(_resultado_nlp(), invalido, valido)

    assert resultado.aplicaciones[0].estado == EstadoAplicacionGuardrail.ERROR
    assert "fragmento inexistente" in resultado.aplicaciones[0].motivo
    assert resultado.aplicaciones[1].estado == EstadoAplicacionGuardrail.APLICADO


def prueba_repositorio_rechaza_codigo_y_version_duplicados() -> None:
    primero = _guardrail("GR-PRUEBA-08", _evaluacion(NivelCobertura.AUSENTE))
    segundo = _guardrail("GR-PRUEBA-08", _evaluacion(NivelCobertura.PARCIAL))

    with pytest.raises(GuardrailDuplicadoError, match="duplicado"):
        RepositorioGuardrailsEnMemoria((primero, segundo))


def prueba_repositorio_admite_versiones_distintas_del_mismo_guardrail() -> None:
    primero = _guardrail("GR-PRUEBA-08", _evaluacion(NivelCobertura.AUSENTE))
    segundo = GuardrailSintetico(
        definicion=_definicion("GR-PRUEBA-08", version=2),
        decision=DecisionAplicabilidad(False, "Version futura no aplicable."),
    )

    repositorio = RepositorioGuardrailsEnMemoria((primero, segundo))

    assert [guardrail.definicion.version for guardrail in repositorio.listar()] == [
        1,
        2,
    ]


def prueba_preserva_orden_y_procesa_solo_versiones_activas() -> None:
    activo_1 = _guardrail("GR-PRUEBA-09", _evaluacion(NivelCobertura.AUSENTE))
    inactivo = _guardrail(
        "GR-PRUEBA-10",
        _evaluacion(NivelCobertura.AUSENTE),
        estado=EstadoGuardrail.INACTIVA,
    )
    activo_2 = _guardrail("GR-PRUEBA-11", _evaluacion(NivelCobertura.AUSENTE))
    repositorio = RepositorioGuardrailsEnMemoria(
        (activo_1, inactivo, activo_2)
    )

    assert repositorio.listar() == (activo_1, inactivo, activo_2)
    _, resultado = _evaluar(
        _resultado_nlp(),
        activo_1,
        inactivo,
        activo_2,
    )
    assert [aplicacion.guardrail_codigo for aplicacion in resultado.aplicaciones] == [
        "GR-PRUEBA-09",
        "GR-PRUEBA-11",
    ]


def prueba_repositorio_vacio_produce_resultado_vacio() -> None:
    _, resultado = _evaluar(_resultado_nlp())

    assert resultado.aplicaciones == ()
    assert resultado.hallazgos == ()


def prueba_contexto_expone_metadatos_inmutables_a_la_aplicabilidad() -> None:
    guardrail = GuardrailSintetico(
        definicion=_definicion("GR-PRUEBA-12"),
        decision=DecisionAplicabilidad(False, "Decision reemplazada."),
        resultado=_evaluacion(NivelCobertura.AUSENTE),
        metadato_requerido="dominio_regulado",
    )

    _, resultado = _evaluar(
        _resultado_nlp(),
        guardrail,
        metadatos={"dominio_regulado": True},
    )

    assert resultado.aplicaciones[0].estado == EstadoAplicacionGuardrail.APLICADO
    assert resultado.metadatos == {"dominio_regulado": True}
    with pytest.raises(TypeError):
        resultado.metadatos["dominio_regulado"] = False

    solicitud = SolicitudEvaluacionEtica(uuid4(), _resultado_nlp(), {"a": 1})
    with pytest.raises(TypeError):
        solicitud.metadatos["a"] = 2


def prueba_mantiene_separados_nivel_prioridad_y_revision_humana() -> None:
    guardrail = _guardrail(
        "GR-PRUEBA-13",
        _evaluacion(
            NivelCobertura.AUSENTE,
            prioridad=PrioridadDocumental.BAJA,
        ),
        revision=True,
    )

    _, resultado = _evaluar(_resultado_nlp(), guardrail)

    hallazgo = resultado.hallazgos[0]
    assert hallazgo.nivel_preliminar == NivelCobertura.AUSENTE
    assert hallazgo.prioridad_documental == PrioridadDocumental.BAJA
    assert hallazgo.requiere_revision_humana is True
    assert "por defecto" in hallazgo.motivo_revision_humana


def prueba_genera_identificadores_y_fechas_utc() -> None:
    guardrail = _guardrail("GR-PRUEBA-14", _evaluacion(NivelCobertura.AUSENTE))

    _, resultado = _evaluar(_resultado_nlp(), guardrail)

    assert isinstance(resultado.analisis_id, UUID)
    assert isinstance(resultado.hallazgos[0].id, UUID)
    assert resultado.fecha_inicio.tzinfo == timezone.utc
    assert resultado.fecha_fin.tzinfo == timezone.utc
    assert resultado.hallazgos[0].fecha_generacion.tzinfo == timezone.utc
    assert resultado.fecha_inicio <= resultado.fecha_fin


@pytest.mark.parametrize(
    "nivel",
    [NivelCobertura.PARCIAL, NivelCobertura.EXPLICITO],
)
def prueba_rechaza_cobertura_positiva_sin_evidencia(
    nivel: NivelCobertura,
) -> None:
    guardrail = _guardrail("GR-PRUEBA-15", _evaluacion(nivel))

    _, resultado = _evaluar(_resultado_nlp(), guardrail)

    assert resultado.aplicaciones[0].estado == EstadoAplicacionGuardrail.ERROR
    assert "requiere evidencia" in resultado.aplicaciones[0].motivo


def prueba_integracion_pipeline_nlp_motor_sin_modificar_resultado() -> None:
    resultado_nlp = analizar_texto(
        "2.1. El sistema deberá registrar cada decisión automatizada."
    )
    fragmento = resultado_nlp.fragmentos_clasificados[0].fragmento
    guardrail = _guardrail(
        "GR-PRUEBA-16",
        _evaluacion(
            NivelCobertura.EXPLICITO,
            ReferenciaEvidencia(
                fragmento.id,
                TipoVinculoEvidencia.SOPORTA,
            ),
        ),
    )

    _, resultado = _evaluar(resultado_nlp, guardrail)

    assert resultado.aplicaciones[0].estado == EstadoAplicacionGuardrail.APLICADO
    assert resultado.hallazgos[0].evidencias[0].texto == fragmento.texto
    assert resultado_nlp.fragmentos_clasificados[0].fragmento is fragmento
