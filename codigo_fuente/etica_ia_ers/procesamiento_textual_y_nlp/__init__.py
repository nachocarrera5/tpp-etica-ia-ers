"""Normalizacion, segmentacion y senales NLP."""

from .errores import (
    ErrorEnPasoDeNormalizacion,
    ErrorNormalizacion,
    PasoDesconocidoError,
    TextoVacioError,
)
from .normalizador import NormalizadorDeTexto

__all__ = [
    "ErrorEnPasoDeNormalizacion",
    "ErrorNormalizacion",
    "NormalizadorDeTexto",
    "PasoDesconocidoError",
    "TextoVacioError",
]
