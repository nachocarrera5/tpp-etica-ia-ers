"""Entrada documental y registro inicial de ERS."""
from .cargador import cargar_documento, cargar_documento_desde_ruta
from .errores import (
    DocumentoIlegibleError,
    DocumentoVacioError,
    ErrorCargaDocumento,
    FormatoNoSoportadoError,
)

__all__ = [
    "DocumentoIlegibleError",
    "DocumentoVacioError",
    "ErrorCargaDocumento",
    "FormatoNoSoportadoError",
    "cargar_documento",
    "cargar_documento_desde_ruta",
]
