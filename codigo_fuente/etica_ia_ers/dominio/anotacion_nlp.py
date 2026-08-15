from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class TipoSenalNLP(str, Enum):
    ACTOR = "ACTOR"
    ACCION = "ACCION"
    CONDICION = "CONDICION"


@dataclass(frozen=True)
class AnotacionNLP:
    fragmento_id: UUID
    tipo_senal: TipoSenalNLP
    valor_detectado: str
    posicion_inicio: int
    posicion_fin: int
    id: UUID = field(default_factory=uuid4)
    confianza: Optional[float] = None
    metadatos: Dict[str, Any] = field(default_factory=dict)
