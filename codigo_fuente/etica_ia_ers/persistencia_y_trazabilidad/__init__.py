"""Persistencia y trazabilidad."""
from .errores import (
    AlmacenamientoCorruptoError,
    DocumentoNoEncontradoError,
    DocumentoYaRegistradoError,
    ErrorAlmacenamiento,
    TextoNormalizadoInvalidoError,
)
from .repositorio import RepositorioDeDocumentos, RepositorioEnMemoria
from .repositorio_archivos import DIRECTORIO_ALMACENAMIENTO, RepositorioEnArchivos
from .trazabilidad import (
    RegistroDeTrazabilidad,
    TrazabilidadEnArchivo,
    TrazabilidadEnMemoria,
)

__all__ = [
    "AlmacenamientoCorruptoError",
    "DIRECTORIO_ALMACENAMIENTO",
    "DocumentoNoEncontradoError",
    "DocumentoYaRegistradoError",
    "ErrorAlmacenamiento",
    "RegistroDeTrazabilidad",
    "RepositorioDeDocumentos",
    "RepositorioEnArchivos",
    "RepositorioEnMemoria",
    "TextoNormalizadoInvalidoError",
    "TrazabilidadEnArchivo",
    "TrazabilidadEnMemoria",
]
