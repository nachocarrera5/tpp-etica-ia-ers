from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TextEnum(str, Enum):
    pass


class Level(TextEnum):
    AUSENTE = "Ausente"
    PARCIAL = "Parcial"
    EXPLICITO = "Explicito"


class Priority(TextEnum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"


class AnalysisStatus(TextEnum):
    REGISTRADO = "Registrado"
    PROCESANDO = "Procesando"
    COMPLETADO = "Completado"
    ERROR = "Error"


@dataclass(frozen=True)
class Document:
    id: str
    nombre_original: str
    formato_origen: str
    contenido_extraido: str
    hash_contenido: str
    metadatos: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisConfig:
    codigo: str
    version: int
    idioma: str
    parametros: dict[str, Any] = field(default_factory=dict)
    activa: bool = True


@dataclass(frozen=True)
class AnalysisRun:
    id: str
    documento_id: str
    configuracion_codigo: str
    configuracion_version: int
    fecha_inicio: datetime
    estado: AnalysisStatus = AnalysisStatus.REGISTRADO
    advertencias: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Fragment:
    id: str
    analisis_id: str
    secuencia_orden: int
    texto: str
    tipo_fragmento: str = "fragmento"
    identificador_ers: str | None = None
    seccion_origen: str | None = None
    posicion_inicio: int | None = None
    posicion_fin: int | None = None


@dataclass(frozen=True)
class Guardrail:
    codigo: str
    nombre: str
    version: int
    estado: str
    familia: str
    descripcion: str
    dimensiones: list[dict[str, Any]]
    criterios: list[str] = field(default_factory=list)
    marcos_referencia: list[str] = field(default_factory=list)
    aplicabilidad: dict[str, Any] = field(default_factory=dict)
    evidencia_esperada: dict[str, Any] = field(default_factory=dict)
    senales: dict[str, Any] = field(default_factory=dict)
    clasificacion: dict[str, str] = field(default_factory=dict)
    prioridad: dict[str, Any] = field(default_factory=dict)
    revision_humana: dict[str, Any] = field(default_factory=dict)
    recomendacion: dict[str, Any] = field(default_factory=dict)
    salida: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Evidence:
    fragmento_id: str
    texto: str
    tipo_vinculo: str
    identificador_ers: str | None = None
    seccion_origen: str | None = None
    observacion: str | None = None


@dataclass(frozen=True)
class Finding:
    id: str
    analisis_id: str
    guardrail_codigo: str
    guardrail_version: int
    dimensiones_asociadas: list[str]
    nivel_preliminar: Level
    prioridad_documental: Priority
    justificacion: str
    requiere_revision_humana: bool
    evidencias: list[Evidence] = field(default_factory=list)


@dataclass(frozen=True)
class Recommendation:
    id: str
    analisis_id: str
    accion_sugerida: str
    fundamento: str
    prioridad_documental: Priority
    tipo_mejora: str
    dimension_codigo: str | None = None
    hallazgo_id: str | None = None
