from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional, Tuple
from uuid import UUID, uuid4

from .guardrail import (
    DimensionEtica,
    FamiliaGuardrail,
    NivelCobertura,
    PrioridadDocumental,
)


class GrupoTematico(str, Enum):
    CONTEXTO_Y_AFECTADOS = "CONTEXTO_Y_AFECTADOS"
    DATOS_Y_TRATO_JUSTO = "DATOS_Y_TRATO_JUSTO"
    COMPRENSION_Y_CONTROL_HUMANO = "COMPRENSION_Y_CONTROL_HUMANO"
    GOBERNANZA_Y_OPERACION_RESPONSABLE = (
        "GOBERNANZA_Y_OPERACION_RESPONSABLE"
    )


_VALORES_NIVEL = {
    NivelCobertura.AUSENTE: 0,
    NivelCobertura.PARCIAL: 1,
    NivelCobertura.EXPLICITO: 2,
}


@dataclass(frozen=True)
class ResultadoDimensionEtica:
    analisis_id: UUID
    dimension: DimensionEtica
    nombre_dimension: str
    grupo_tematico: GrupoTematico
    nivel_consolidado: NivelCobertura
    prioridad_documental: PrioridadDocumental
    justificacion: str
    hallazgos_relacionados: Tuple[UUID, ...]
    brechas_principales: Tuple[str, ...] = ()
    requiere_revision_humana: bool = False
    motivo_revision_humana: Optional[str] = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "hallazgos_relacionados", tuple(self.hallazgos_relacionados)
        )
        object.__setattr__(
            self, "brechas_principales", tuple(self.brechas_principales)
        )
        if not self.nombre_dimension.strip():
            raise ValueError("El nombre de la dimension no puede estar vacio.")
        if not self.justificacion.strip():
            raise ValueError("El resultado requiere una justificacion.")
        if not self.hallazgos_relacionados:
            raise ValueError("El resultado requiere hallazgos relacionados.")
        if self.requiere_revision_humana and not (
            self.motivo_revision_humana or ""
        ).strip():
            raise ValueError("La revision humana requiere un motivo.")

    @property
    def valor_auxiliar(self) -> int:
        return _VALORES_NIVEL[self.nivel_consolidado]


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


@dataclass(frozen=True)
class IndicadoresGrupoTematico:
    grupo_tematico: GrupoTematico
    dimensiones_incluidas: Tuple[DimensionEtica, ...]
    dimensiones_evaluadas: Tuple[DimensionEtica, ...]
    ausentes: int
    parciales: int
    explicitas: int
    prioridad_maxima: Optional[PrioridadDocumental]
    requiere_revision_humana: bool
    brechas_principales: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "dimensiones_incluidas", tuple(self.dimensiones_incluidas)
        )
        object.__setattr__(
            self, "dimensiones_evaluadas", tuple(self.dimensiones_evaluadas)
        )
        object.__setattr__(
            self, "brechas_principales", tuple(self.brechas_principales)
        )


@dataclass(frozen=True)
class IndicadoresGuardrails:
    total_guardrails: int
    guardrails_aplicados: int
    guardrails_no_aplicables: int
    guardrails_con_error: int
    familias_guardrail_cubiertas: Tuple[FamiliaGuardrail, ...]
    hallazgos_por_familia: Mapping[FamiliaGuardrail, int]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "familias_guardrail_cubiertas",
            tuple(self.familias_guardrail_cubiertas),
        )
        object.__setattr__(
            self,
            "hallazgos_por_familia",
            MappingProxyType(dict(self.hallazgos_por_familia)),
        )


@dataclass(frozen=True)
class IndicadoresPrioridad:
    hallazgos_prioridad_alta: int
    hallazgos_prioridad_media: int
    hallazgos_prioridad_baja: int
    dimensiones_prioridad_alta: Tuple[DimensionEtica, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dimensiones_prioridad_alta",
            tuple(self.dimensiones_prioridad_alta),
        )


@dataclass(frozen=True)
class ResultadoCoberturaEtica:
    analisis_id: UUID
    documento_id: UUID
    fecha_generacion: datetime
    resultados_por_dimension: Tuple[ResultadoDimensionEtica, ...]
    indicadores_globales: IndicadoresGlobales
    indicadores_por_grupo: Tuple[IndicadoresGrupoTematico, ...]
    indicadores_guardrails: IndicadoresGuardrails
    indicadores_prioridad: IndicadoresPrioridad
    dimensiones_no_evaluadas: Tuple[DimensionEtica, ...]
    advertencias: Tuple[str, ...] = ()
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resultados_por_dimension",
            tuple(self.resultados_por_dimension),
        )
        object.__setattr__(
            self, "indicadores_por_grupo", tuple(self.indicadores_por_grupo)
        )
        object.__setattr__(
            self,
            "dimensiones_no_evaluadas",
            tuple(self.dimensiones_no_evaluadas),
        )
        object.__setattr__(self, "advertencias", tuple(self.advertencias))
