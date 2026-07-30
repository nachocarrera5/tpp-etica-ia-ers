"""Normalizacion, segmentacion y senales NLP."""

from .errores import (
    ErrorEnPasoDeNormalizacion,
    ErrorNormalizacion,
    PasoDesconocidoError,
    TextoVacioError,
)
from .normalizador import NormalizadorDeTexto
from .segmentador import segmentar

__all__ = [
    "ErrorEnPasoDeNormalizacion",
    "ErrorNormalizacion",
    "NormalizadorDeTexto",
    "PasoDesconocidoError",
    "TextoVacioError",
    "segmentar",
]
