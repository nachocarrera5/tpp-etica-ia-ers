"""Entidades de la bitacora de trazabilidad del prototipo."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict
from uuid import UUID


class AccionTrazabilidad(str, Enum):
    """Acciones registrables sobre un documento almacenado."""

    CARGA = "CARGA"
    NORMALIZACION = "NORMALIZACION"
    CAMBIO_ESTADO = "CAMBIO_ESTADO"
    ELIMINACION = "ELIMINACION"


@dataclass(frozen=True)
class EventoTrazabilidad:
    """Hecho registrado sobre un documento, con su fecha y detalle."""

    id_documento: UUID
    accion: AccionTrazabilidad
    fecha: datetime
    detalle: Dict[str, Any] = field(default_factory=dict)
