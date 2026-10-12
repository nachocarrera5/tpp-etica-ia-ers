from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Optional, Tuple


class DimensionEtica(str, Enum):
    D01 = "D01"
    D02 = "D02"
    D03 = "D03"
    D04 = "D04"
    D05 = "D05"
    D06 = "D06"
    D07 = "D07"
    D08 = "D08"
    D09 = "D09"
    D10 = "D10"


class FamiliaGuardrail(str, Enum):
    PRESENCIA = "G-PRES"
    DELIMITACION = "G-DELIM"
    VERIFICABILIDAD = "G-VERIF"
    RESPONSABILIDAD = "G-RESP"
    CONTROL = "G-CTRL"
    CALIDAD_DOCUMENTAL = "G-QUAL"


class EstadoGuardrail(str, Enum):
    ACTIVA = "ACTIVA"
    INACTIVA = "INACTIVA"
    EXPERIMENTAL = "EXPERIMENTAL"
    ARCHIVADA = "ARCHIVADA"


class NivelCobertura(str, Enum):
    AUSENTE = "AUSENTE"
    PARCIAL = "PARCIAL"
    EXPLICITO = "EXPLICITO"


class PrioridadDocumental(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


# Peso por defecto de cada guardrail en la cobertura ponderada. Deriva de la
# prioridad documental, que ya expresa la criticidad del criterio verificado.
PESO_POR_PRIORIDAD = MappingProxyType(
    {
        PrioridadDocumental.BAJA: 1.0,
        PrioridadDocumental.MEDIA: 2.0,
        PrioridadDocumental.ALTA: 3.0,
    }
)


class EstadoAplicacionGuardrail(str, Enum):
    APLICADO = "APLICADO"
    NO_APLICABLE = "NO_APLICABLE"
    ERROR = "ERROR"


class TipoVinculoEvidencia(str, Enum):
    SOPORTA = "SOPORTA"
    CONTRADICE = "CONTRADICE"
    CONTEXTUALIZA = "CONTEXTUALIZA"


_PATRON_CODIGO_GUARDRAIL = re.compile(r"^GR-[A-Z0-9]+(?:-[A-Z0-9]+)*$")


@dataclass(frozen=True)
class IdentidadGuardrailVersionada:
    codigo: str
    version: int

    def __post_init__(self) -> None:
        if not _PATRON_CODIGO_GUARDRAIL.fullmatch(self.codigo):
            raise ValueError(
                "El codigo del guardrail debe respetar el formato GR-..."
            )
        if self.version < 1:
            raise ValueError("La version del guardrail debe ser positiva.")


@dataclass(frozen=True)
class DefinicionGuardrail:
    codigo: str
    nombre: str
    version: int
    estado: EstadoGuardrail
    familia: FamiliaGuardrail
    dimensiones: Tuple[DimensionEtica, ...]
    descripcion: str
    criterios: Tuple[str, ...] = ()
    prioridad_base: PrioridadDocumental = PrioridadDocumental.MEDIA
    requiere_revision_por_defecto: bool = False
    peso: Optional[float] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimensiones", tuple(self.dimensiones))
        object.__setattr__(self, "criterios", tuple(self.criterios))
        IdentidadGuardrailVersionada(self.codigo, self.version)
        if not self.nombre.strip():
            raise ValueError("El nombre del guardrail no puede estar vacio.")
        if not self.dimensiones:
            raise ValueError("El guardrail debe asociarse con alguna dimension.")
        if len(set(self.dimensiones)) != len(self.dimensiones):
            raise ValueError("Las dimensiones del guardrail no pueden repetirse.")
        if not self.descripcion.strip():
            raise ValueError("La descripcion del guardrail no puede estar vacia.")
        if len(set(self.criterios)) != len(self.criterios):
            raise ValueError("Los criterios del guardrail no pueden repetirse.")
        if any(not criterio.strip() for criterio in self.criterios):
            raise ValueError("Los criterios del guardrail no pueden estar vacios.")
        if self.peso is not None and self.peso <= 0:
            raise ValueError("El peso del guardrail debe ser positivo.")

    @property
    def peso_efectivo(self) -> float:
        """Peso explicito del catalogo o, si no se definio, el de su prioridad."""
        if self.peso is not None:
            return self.peso
        return PESO_POR_PRIORIDAD[self.prioridad_base]

    @property
    def identidad_versionada(self) -> IdentidadGuardrailVersionada:
        return IdentidadGuardrailVersionada(self.codigo, self.version)

    @property
    def clave_versionada(self) -> Tuple[str, int]:
        identidad = self.identidad_versionada
        return identidad.codigo, identidad.version
