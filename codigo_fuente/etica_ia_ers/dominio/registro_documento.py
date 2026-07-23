"""Entidades del registro persistente de una ERS y su estado de analisis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict
from uuid import UUID

from .documento import DocumentoERS, FormatoDocumento


class EstadoAnalisis(str, Enum):
    """Etapa del flujo entrada -> NLP -> motor alcanzada por la ERS."""

    CARGADO = "CARGADO"
    NORMALIZADO = "NORMALIZADO"
    EVALUADO = "EVALUADO"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ResumenDocumento:
    """Vista liviana de un documento almacenado, sin su contenido textual."""

    id: UUID
    nombre_original: str
    formato_origen: FormatoDocumento
    hash_contenido: str
    fecha_carga: datetime
    estado: EstadoAnalisis
    fecha_actualizacion: datetime
    metadatos: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RegistroDocumento:
    """Documento almacenado junto con el estado de su analisis."""

    documento: DocumentoERS
    estado: EstadoAnalisis
    fecha_actualizacion: datetime

    @property
    def id(self) -> UUID:
        return self.documento.id

    @property
    def resumen(self) -> ResumenDocumento:
        return ResumenDocumento(
            id=self.documento.id,
            nombre_original=self.documento.nombre_original,
            formato_origen=self.documento.formato_origen,
            hash_contenido=self.documento.hash_contenido,
            fecha_carga=self.documento.fecha_carga,
            estado=self.estado,
            fecha_actualizacion=self.fecha_actualizacion,
            metadatos=dict(self.documento.metadatos),
        )
