from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Pattern, Tuple
from uuid import UUID

from etica_ia_ers.dominio import (
    ContextoEvaluacionEtica,
    DecisionAplicabilidad,
    DefinicionGuardrail,
    EvaluacionPreliminarGuardrail,
    FragmentoDocumental,
    NivelCobertura,
    PrioridadDocumental,
    ReferenciaEvidencia,
    TipoFragmento,
    TipoVinculoEvidencia,
)


@dataclass(frozen=True)
class SenalLexica:

    nombre: str
    patron: Pattern[str]


def senal(nombre: str, expresion: str) -> SenalLexica:
    return SenalLexica(nombre, re.compile(rf"(?<!\w)(?:{expresion})(?!\w)"))


def _normalizar_para_busqueda(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.casefold())
    sin_acentos = "".join(
        caracter
        for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"\s+", " ", sin_acentos).strip()


def _fragmentos_evaluables(
    contexto: ContextoEvaluacionEtica,
) -> Tuple[FragmentoDocumental, ...]:
    return tuple(
        clasificado.fragmento
        for clasificado in contexto.resultado_nlp.fragmentos_clasificados
        if clasificado.fragmento.tipo_fragmento != TipoFragmento.ENCABEZADO
    )


def _buscar_coincidencias(
    fragmentos: Tuple[FragmentoDocumental, ...],
    senales: Tuple[SenalLexica, ...],
) -> "Dict[UUID, List[str]]":
    coincidencias: Dict[UUID, List[str]] = {}
    for fragmento in fragmentos:
        texto = _normalizar_para_busqueda(fragmento.texto)
        nombres = [s.nombre for s in senales if s.patron.search(texto)]
        if nombres:
            coincidencias[fragmento.id] = nombres
    return coincidencias


def _crear_evidencias(
    coincidencias: "Dict[UUID, List[str]]",
) -> Tuple[ReferenciaEvidencia, ...]:
    return tuple(
        ReferenciaEvidencia(
            fragmento_id=fragmento_id,
            tipo_vinculo=TipoVinculoEvidencia.SOPORTA,
            observacion="Senales detectadas: " + ", ".join(sorted(set(nombres))),
        )
        for fragmento_id, nombres in coincidencias.items()
    )


@dataclass(frozen=True)
class GuardrailLexico:

    definicion: DefinicionGuardrail
    senales_explicitas: Tuple[SenalLexica, ...] = ()
    senales_parciales: Tuple[SenalLexica, ...] = ()

    def decidir_aplicabilidad(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> DecisionAplicabilidad:
        fragmentos = _fragmentos_evaluables(contexto)
        if not fragmentos:
            return DecisionAplicabilidad(
                aplica=False,
                motivo=(
                    "El documento no contiene fragmentos evaluables "
                    "distintos de encabezados."
                ),
            )
        return DecisionAplicabilidad(
            aplica=True,
            motivo="El documento contiene fragmentos evaluables para la dimension.",
        )

    def evaluar(
        self,
        contexto: ContextoEvaluacionEtica,
    ) -> EvaluacionPreliminarGuardrail:
        fragmentos = _fragmentos_evaluables(contexto)

        explicitas = _buscar_coincidencias(fragmentos, self.senales_explicitas)
        if explicitas:
            nombres = sorted({n for lista in explicitas.values() for n in lista})
            return EvaluacionPreliminarGuardrail(
                nivel=NivelCobertura.EXPLICITO,
                justificacion=(
                    "Se hallo evidencia documental clara y localizada: "
                    + ", ".join(nombres)
                    + "."
                ),
                prioridad=PrioridadDocumental.BAJA,
                justificacion_prioridad=(
                    "La evidencia es explicita, pero requiere validacion "
                    "humana por contexto o dominio."
                ),
                evidencias=_crear_evidencias(explicitas),
                requiere_revision_humana=True,
                motivo_revision_humana=(
                    "Un nivel Explicito no certifica adecuacion real de "
                    "datos, privacidad o equidad; requiere revision humana."
                ),
            )

        parciales = _buscar_coincidencias(fragmentos, self.senales_parciales)
        if parciales:
            nombres = sorted({n for lista in parciales.values() for n in lista})
            return EvaluacionPreliminarGuardrail(
                nivel=NivelCobertura.PARCIAL,
                justificacion=(
                    "Se hallo evidencia generica, incompleta o ambigua: "
                    + ", ".join(nombres)
                    + "."
                ),
                prioridad=PrioridadDocumental.MEDIA,
                justificacion_prioridad=(
                    "La mencion es generica; faltan responsables, metricas "
                    "o acciones correctivas verificables."
                ),
                evidencias=_crear_evidencias(parciales),
                requiere_revision_humana=True,
                motivo_revision_humana=(
                    "La evidencia parcial requiere revision humana para "
                    "completar o verificar la especificacion."
                ),
            )

        return EvaluacionPreliminarGuardrail(
            nivel=NivelCobertura.AUSENTE,
            justificacion=(
                "No se hallo evidencia documental relevante para este "
                "guardrail."
            ),
            prioridad=PrioridadDocumental.ALTA,
            justificacion_prioridad=(
                "La ausencia de evidencia documental amerita revision "
                "prioritaria temprana."
            ),
            evidencias=(),
            requiere_revision_humana=True,
            motivo_revision_humana=(
                "La ausencia de evidencia debe confirmarse con el "
                "responsable de la especificacion."
            ),
        )
