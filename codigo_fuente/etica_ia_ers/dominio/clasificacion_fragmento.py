from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from .fragmento import FragmentoDocumental


class TipoClasificacionFragmento(str, Enum):
    REQUISITO_FUNCIONAL = "REQUISITO_FUNCIONAL"
    REQUISITO_NO_FUNCIONAL = "REQUISITO_NO_FUNCIONAL"
    RESTRICCION = "RESTRICCION"
    CONTEXTO = "CONTEXTO"
    OTRO = "OTRO"


@dataclass(frozen=True)
class FragmentoClasificado:
    fragmento: FragmentoDocumental
    clasificacion: TipoClasificacionFragmento
    senales: Tuple[str, ...]
    justificacion: str
