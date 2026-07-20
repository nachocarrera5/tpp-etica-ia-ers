from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict
from uuid import UUID


class FormatoDocumento(str, Enum):
    TXT = "TXT"
    PDF = "PDF"
    DOCX = "DOCX"


@dataclass(frozen=True)
class DocumentoERS:
    id: UUID
    nombre_original: str
    formato_origen: FormatoDocumento
    contenido_extraido: str
    hash_contenido: str
    fecha_carga: datetime
    metadatos: Dict[str, Any] = field(default_factory=dict)
