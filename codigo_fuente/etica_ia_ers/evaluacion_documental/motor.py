from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Sequence, Tuple
from uuid import UUID, uuid4

from etica_ia_ers.dominio import (
    ContextoEvaluacionEtica,
    DefinicionGuardrail,
    EstadoAplicacionGuardrail,
    EstadoGuardrail,
    EvaluacionPreliminarGuardrail,
    EvidenciaHallazgo,
    FragmentoDocumental,
    HallazgoEvaluacion,
    NivelCobertura,
    ResultadoAplicacionGuardrail,
    ResultadoEvaluacionEtica,
    SolicitudEvaluacionEtica,
)
from etica_ia_ers.modelo_etico_y_guardrails import (
    GuardrailEvaluable,
    RepositorioGuardrails,
)

from .errores import EvidenciaInvalidaError, EvaluacionGuardrailInvalidaError


class MotorEvaluacionEtica:
    def __init__(self, repositorio: RepositorioGuardrails) -> None:
        self._repositorio = repositorio

    def evaluar(
        self,
        solicitud: SolicitudEvaluacionEtica,
    ) -> ResultadoEvaluacionEtica:
        fecha_inicio = datetime.now(timezone.utc)
        analisis_id = uuid4()
        contexto = ContextoEvaluacionEtica(
            analisis_id=analisis_id,
            documento_id=solicitud.documento_id,
            resultado_nlp=solicitud.resultado_nlp,
            metadatos=solicitud.metadatos,
        )
        fragmentos = self._indexar_fragmentos(solicitud)
        aplicaciones: List[ResultadoAplicacionGuardrail] = []
        guardrails = self._repositorio.listar()

        for guardrail in guardrails:
            definicion = guardrail.definicion
            if definicion.estado != EstadoGuardrail.ACTIVA:
                continue

            try:
                decision = guardrail.decidir_aplicabilidad(contexto)
                if not decision.aplica:
                    aplicaciones.append(
                        ResultadoAplicacionGuardrail(
                            guardrail_codigo=definicion.codigo,
                            guardrail_version=definicion.version,
                            estado=EstadoAplicacionGuardrail.NO_APLICABLE,
                            motivo=decision.motivo,
                        )
                    )
                    continue

                evaluacion = guardrail.evaluar(contexto)
                hallazgo = self._crear_hallazgo(
                    contexto,
                    guardrail.definicion,
                    evaluacion,
                    fragmentos,
                )
                aplicaciones.append(
                    ResultadoAplicacionGuardrail(
                        guardrail_codigo=definicion.codigo,
                        guardrail_version=definicion.version,
                        estado=EstadoAplicacionGuardrail.APLICADO,
                        motivo=decision.motivo,
                        hallazgo=hallazgo,
                    )
                )
            except Exception as error:
                aplicaciones.append(
                    ResultadoAplicacionGuardrail(
                        guardrail_codigo=definicion.codigo,
                        guardrail_version=definicion.version,
                        estado=EstadoAplicacionGuardrail.ERROR,
                        motivo=f"{type(error).__name__}: {error}",
                    )
                )

        return ResultadoEvaluacionEtica(
            analisis_id=analisis_id,
            documento_id=solicitud.documento_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=datetime.now(timezone.utc),
            aplicaciones=tuple(aplicaciones),
            advertencias=self._advertencias_dominio(contexto, guardrails),
            metadatos=solicitud.metadatos,
        )

    @staticmethod
    def _advertencias_dominio(
        contexto: ContextoEvaluacionEtica,
        guardrails: Sequence[GuardrailEvaluable],
    ) -> Tuple[str, ...]:
        declarado = contexto.metadatos.get("dominio")
        if (
            not isinstance(declarado, str)
            or not declarado.strip()
            or contexto.dominio_aplicacion is not None
            or not any(
                guardrail.definicion.es_especifico_de_dominio
                for guardrail in guardrails
            )
        ):
            return ()
        return (
            f"El dominio declarado '{declarado.strip()}' no tiene guardrails "
            "especificos en el catalogo; se aplicaron solo los guardrails "
            "generales.",
        )

    @staticmethod
    def _indexar_fragmentos(
        solicitud: SolicitudEvaluacionEtica,
    ) -> Dict[UUID, FragmentoDocumental]:
        fragmentos: Dict[UUID, FragmentoDocumental] = {}
        for clasificado in solicitud.resultado_nlp.fragmentos_clasificados:
            fragmento = clasificado.fragmento
            if fragmento.id in fragmentos:
                raise EvidenciaInvalidaError(
                    f"El fragmento {fragmento.id} aparece mas de una vez."
                )
            fragmentos[fragmento.id] = fragmento
        return fragmentos

    @staticmethod
    def _crear_hallazgo(
        contexto: ContextoEvaluacionEtica,
        definicion: DefinicionGuardrail,
        evaluacion: EvaluacionPreliminarGuardrail,
        fragmentos: Dict[UUID, FragmentoDocumental],
    ) -> HallazgoEvaluacion:
        if (
            evaluacion.nivel != NivelCobertura.AUSENTE
            and not evaluacion.evidencias
        ):
            raise EvaluacionGuardrailInvalidaError(
                "Un nivel parcial o explicito requiere evidencia."
            )

        evidencias: List[EvidenciaHallazgo] = []
        referencias_vistas = set()
        for referencia in evaluacion.evidencias:
            clave = (referencia.fragmento_id, referencia.tipo_vinculo)
            if clave in referencias_vistas:
                raise EvidenciaInvalidaError(
                    "La misma evidencia y vinculo no pueden repetirse."
                )
            referencias_vistas.add(clave)

            fragmento = fragmentos.get(referencia.fragmento_id)
            if fragmento is None:
                raise EvidenciaInvalidaError(
                    "La evidencia referencia un fragmento inexistente: "
                    f"{referencia.fragmento_id}."
                )
            evidencias.append(
                EvidenciaHallazgo(
                    fragmento_id=fragmento.id,
                    identificador_ers=fragmento.identificador_ers,
                    seccion_origen=fragmento.seccion_origen,
                    texto=fragmento.texto,
                    posicion_inicio=fragmento.posicion_inicio,
                    posicion_fin=fragmento.posicion_fin,
                    tipo_vinculo=referencia.tipo_vinculo,
                    relevancia=referencia.relevancia,
                    observacion=referencia.observacion,
                    fragmentos_clave=referencia.fragmentos_clave,
                )
            )

        requiere_revision = (
            definicion.requiere_revision_por_defecto
            or evaluacion.requiere_revision_humana
        )
        motivo_revision = evaluacion.motivo_revision_humana
        if requiere_revision and not motivo_revision:
            motivo_revision = "El guardrail requiere revision humana por defecto."

        return HallazgoEvaluacion(
            analisis_id=contexto.analisis_id,
            guardrail_codigo=definicion.codigo,
            guardrail_version=definicion.version,
            familia_guardrail=definicion.familia,
            dimensiones_asociadas=definicion.dimensiones,
            criterios_asociados=definicion.criterios,
            nivel_preliminar=evaluacion.nivel,
            prioridad_documental=evaluacion.prioridad,
            justificacion=evaluacion.justificacion,
            justificacion_prioridad=evaluacion.justificacion_prioridad,
            requiere_revision_humana=requiere_revision,
            motivo_revision_humana=motivo_revision,
            evidencias=tuple(evidencias),
            fecha_generacion=datetime.now(timezone.utc),
            guardrail_nombre=definicion.nombre,
            guardrail_descripcion=definicion.descripcion,
            peso=definicion.peso_efectivo,
            guardrail_dominios=definicion.dominios,
        )
