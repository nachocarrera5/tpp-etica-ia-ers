from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple
from uuid import UUID, uuid4

from .guardrail import (
    DimensionEtica,
    EstadoAplicacionGuardrail,
    FamiliaGuardrail,
    NivelCobertura,
    PrioridadDocumental,
    TipoVinculoEvidencia,
)
from .resultado_analisis_nlp import ResultadoAnalisisNLP


def _metadatos_inmutables(
    metadatos: Mapping[str, Any],
) -> Mapping[str, Any]:
    return MappingProxyType(dict(metadatos))


@dataclass(frozen=True)
class SolicitudEvaluacionEtica:
    documento_id: UUID
    resultado_nlp: ResultadoAnalisisNLP
    metadatos: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadatos",
            _metadatos_inmutables(self.metadatos),
        )


@dataclass(frozen=True)
class ContextoEvaluacionEtica:
    analisis_id: UUID
    documento_id: UUID
    resultado_nlp: ResultadoAnalisisNLP
    metadatos: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadatos",
            _metadatos_inmutables(self.metadatos),
        )


@dataclass(frozen=True)
class DecisionAplicabilidad:
    aplica: bool
    motivo: str

    def __post_init__(self) -> None:
        if not self.motivo.strip():
            raise ValueError("La decision de aplicabilidad requiere un motivo.")


@dataclass(frozen=True)
class ReferenciaEvidencia:
    fragmento_id: UUID
    tipo_vinculo: TipoVinculoEvidencia
    relevancia: Optional[float] = None
    observacion: Optional[str] = None
    fragmentos_clave: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "fragmentos_clave", tuple(self.fragmentos_clave)
        )
        if self.relevancia is not None and not 0 <= self.relevancia <= 1:
            raise ValueError("La relevancia debe estar entre 0 y 1.")


@dataclass(frozen=True)
class EvaluacionPreliminarGuardrail:
    nivel: NivelCobertura
    justificacion: str
    prioridad: PrioridadDocumental
    justificacion_prioridad: str
    evidencias: Tuple[ReferenciaEvidencia, ...] = ()
    requiere_revision_humana: bool = False
    motivo_revision_humana: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidencias", tuple(self.evidencias))
        if not self.justificacion.strip():
            raise ValueError("La evaluacion requiere una justificacion.")
        if not self.justificacion_prioridad.strip():
            raise ValueError("La prioridad requiere una justificacion.")
        if (
            self.requiere_revision_humana
            and not (self.motivo_revision_humana or "").strip()
        ):
            raise ValueError("La revision humana requiere un motivo.")


@dataclass(frozen=True)
class EvidenciaHallazgo:
    fragmento_id: UUID
    identificador_ers: Optional[str]
    seccion_origen: Optional[str]
    texto: str
    posicion_inicio: Optional[int]
    posicion_fin: Optional[int]
    tipo_vinculo: TipoVinculoEvidencia
    relevancia: Optional[float] = None
    observacion: Optional[str] = None
    fragmentos_clave: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "fragmentos_clave", tuple(self.fragmentos_clave)
        )


@dataclass(frozen=True)
class HallazgoEvaluacion:
    analisis_id: UUID
    guardrail_codigo: str
    guardrail_version: int
    familia_guardrail: FamiliaGuardrail
    dimensiones_asociadas: Tuple[DimensionEtica, ...]
    criterios_asociados: Tuple[str, ...]
    nivel_preliminar: NivelCobertura
    prioridad_documental: PrioridadDocumental
    justificacion: str
    justificacion_prioridad: str
    requiere_revision_humana: bool
    motivo_revision_humana: Optional[str]
    evidencias: Tuple[EvidenciaHallazgo, ...]
    fecha_generacion: datetime
    guardrail_nombre: Optional[str] = None
    guardrail_descripcion: Optional[str] = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dimensiones_asociadas",
            tuple(self.dimensiones_asociadas),
        )
        object.__setattr__(
            self,
            "criterios_asociados",
            tuple(self.criterios_asociados),
        )
        object.__setattr__(self, "evidencias", tuple(self.evidencias))


@dataclass(frozen=True)
class ResultadoAplicacionGuardrail:
    guardrail_codigo: str
    guardrail_version: int
    estado: EstadoAplicacionGuardrail
    motivo: str
    hallazgo: Optional[HallazgoEvaluacion] = None

    def __post_init__(self) -> None:
        if not self.motivo.strip():
            raise ValueError("La aplicacion del guardrail requiere un motivo.")
        if self.estado == EstadoAplicacionGuardrail.APLICADO:
            if self.hallazgo is None:
                raise ValueError("Una aplicacion exitosa requiere un hallazgo.")
        elif self.hallazgo is not None:
            raise ValueError(
                "Una aplicacion no exitosa no puede contener un hallazgo."
            )


@dataclass(frozen=True)
class ResultadoEvaluacionEtica:
    analisis_id: UUID
    documento_id: UUID
    fecha_inicio: datetime
    fecha_fin: datetime
    aplicaciones: Tuple[ResultadoAplicacionGuardrail, ...]
    advertencias: Tuple[str, ...] = ()
    metadatos: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "aplicaciones", tuple(self.aplicaciones))
        object.__setattr__(self, "advertencias", tuple(self.advertencias))
        object.__setattr__(
            self,
            "metadatos",
            _metadatos_inmutables(self.metadatos),
        )

    @property
    def hallazgos(self) -> Tuple[HallazgoEvaluacion, ...]:
        return tuple(
            aplicacion.hallazgo
            for aplicacion in self.aplicaciones
            if aplicacion.hallazgo is not None
        )
