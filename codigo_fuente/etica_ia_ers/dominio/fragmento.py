from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
    seccion_origen: Optional[str] = None
    identificador_ers: Optional[str] = None
    posicion_inicio: Optional[int] = None
    posicion_fin: Optional[int] = None
