from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class TipoFragmento(str, Enum):

    ENCABEZADO = "ENCABEZADO"
    REQUISITO = "REQUISITO"
    ITEM_LISTA = "ITEM_LISTA"
    PARRAFO = "PARRAFO"


@dataclass(frozen=True)
class FragmentoDocumental:
    secuencia_orden: int
    tipo_fragmento: TipoFragmento
    texto: str
    id: UUID = field(default_factory=uuid4)
    seccion_origen: Optional[str] = None
    identificador_ers: Optional[str] = None
    posicion_inicio: Optional[int] = None
    posicion_fin: Optional[int] = None
