from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple
from uuid import UUID, uuid4

from .guardrail import DimensionEtica, NivelCobertura, PrioridadDocumental


class TipoMejora(str, Enum):
    INCORPORAR = "INCORPORAR"
    PRECISAR = "PRECISAR"
    VERIFICAR = "VERIFICAR"
    ASIGNAR_RESPONSABLE = "ASIGNAR_RESPONSABLE"
    MITIGAR = "MITIGAR"
    REGISTRAR = "REGISTRAR"
    OTRA = "OTRA"


@dataclass(frozen=True)
class RecomendacionDocumental:
    analisis_id: UUID
    resultado_dimension_id: UUID
    dimension: DimensionEtica
    hallazgos_relacionados: Tuple[UUID, ...]
    accion_sugerida: str
    fundamento: str
    prioridad_documental: PrioridadDocumental
    tipo_mejora: TipoMejora
    plantilla_version: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "hallazgos_relacionados", tuple(self.hallazgos_relacionados)
        )
        if not self.hallazgos_relacionados:
            raise ValueError("La recomendacion requiere hallazgos relacionados.")
        if len(set(self.hallazgos_relacionados)) != len(
            self.hallazgos_relacionados
        ):
            raise ValueError("Los hallazgos relacionados no pueden repetirse.")
        if not self.accion_sugerida.strip():
            raise ValueError("La recomendacion requiere una accion sugerida.")
        if not self.fundamento.strip():
            raise ValueError("La recomendacion requiere un fundamento.")
        if not self.plantilla_version.strip():
            raise ValueError("La recomendacion requiere una version de plantilla.")


@dataclass(frozen=True)
class AlertaDocumental:
    analisis_id: UUID
    documento_id: UUID
    resultado_dimension_id: UUID
    dimension: DimensionEtica
    nivel_cobertura: NivelCobertura
    prioridad_documental: PrioridadDocumental
    titulo: str
    descripcion: str
    brechas: Tuple[str, ...]
    hallazgos_relacionados: Tuple[UUID, ...]
    recomendaciones_asociadas: Tuple[UUID, ...]
    requiere_revision_humana: bool
    motivo_revision_humana: Optional[str] = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(self, "brechas", tuple(self.brechas))
        object.__setattr__(
            self, "hallazgos_relacionados", tuple(self.hallazgos_relacionados)
        )
        object.__setattr__(
            self,
            "recomendaciones_asociadas",
            tuple(self.recomendaciones_asociadas),
        )
        if self.nivel_cobertura == NivelCobertura.EXPLICITO:
            raise ValueError("Una dimension explicita no debe generar alertas.")
        if not self.titulo.strip() or not self.descripcion.strip():
            raise ValueError("La alerta requiere titulo y descripcion.")
        if not self.hallazgos_relacionados:
            raise ValueError("La alerta requiere hallazgos relacionados.")
        if len(set(self.hallazgos_relacionados)) != len(
            self.hallazgos_relacionados
        ):
            raise ValueError("Los hallazgos relacionados no pueden repetirse.")
        if not self.recomendaciones_asociadas:
            raise ValueError("La alerta requiere recomendaciones asociadas.")
        if len(set(self.recomendaciones_asociadas)) != len(
            self.recomendaciones_asociadas
        ):
            raise ValueError("Las recomendaciones asociadas no pueden repetirse.")
        if self.requiere_revision_humana and not (
            self.motivo_revision_humana or ""
        ).strip():
            raise ValueError("La revision humana requiere un motivo.")


@dataclass(frozen=True)
class ResultadoAlertasYRecomendaciones:
    analisis_id: UUID
    documento_id: UUID
    fecha_generacion: datetime
    alertas: Tuple[AlertaDocumental, ...]
    recomendaciones: Tuple[RecomendacionDocumental, ...]
    advertencias: Tuple[str, ...] = ()
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(self, "alertas", tuple(self.alertas))
        object.__setattr__(self, "recomendaciones", tuple(self.recomendaciones))
        object.__setattr__(self, "advertencias", tuple(self.advertencias))

        if (
            self.fecha_generacion.tzinfo is None
            or self.fecha_generacion.utcoffset() != timedelta(0)
        ):
            raise ValueError("La fecha de generacion debe estar expresada en UTC.")
        if len({alerta.id for alerta in self.alertas}) != len(self.alertas):
            raise ValueError("Las alertas no pueden repetirse.")
        if len({r.id for r in self.recomendaciones}) != len(
            self.recomendaciones
        ):
            raise ValueError("Las recomendaciones no pueden repetirse.")

        recomendaciones = {r.id: r for r in self.recomendaciones}
        for recomendacion in self.recomendaciones:
            if recomendacion.analisis_id != self.analisis_id:
                raise ValueError(
                    "Las recomendaciones deben pertenecer al mismo analisis."
                )
        dimensiones_alertadas = set()
        recomendaciones_referenciadas = set()
        for alerta in self.alertas:
            if (
                alerta.analisis_id != self.analisis_id
                or alerta.documento_id != self.documento_id
            ):
                raise ValueError(
                    "Las alertas deben pertenecer al mismo analisis y documento."
                )
            if alerta.dimension in dimensiones_alertadas:
                raise ValueError("Solo puede existir una alerta por dimension.")
            dimensiones_alertadas.add(alerta.dimension)
            for recomendacion_id in alerta.recomendaciones_asociadas:
                recomendaciones_referenciadas.add(recomendacion_id)
                recomendacion = recomendaciones.get(recomendacion_id)
                if recomendacion is None:
                    raise ValueError(
                        "La alerta referencia una recomendacion inexistente."
                    )
                if (
                    recomendacion.dimension != alerta.dimension
                    or recomendacion.resultado_dimension_id
                    != alerta.resultado_dimension_id
                ):
                    raise ValueError(
                        "La alerta y su recomendacion deben referir a la misma "
                        "dimension."
                    )
                if (
                    recomendacion.hallazgos_relacionados
                    != alerta.hallazgos_relacionados
                ):
                    raise ValueError(
                        "La alerta y su recomendacion deben referir a los mismos "
                        "hallazgos."
                    )
        if recomendaciones_referenciadas != set(recomendaciones):
            raise ValueError("No puede haber recomendaciones sin una alerta.")
