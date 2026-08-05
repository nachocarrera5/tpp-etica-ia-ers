"""Normalizacion, segmentacion y senales NLP."""

from .clasificador import clasificar_fragmento, clasificar_fragmentos
from .errores import (
    ErrorEnPasoDeNormalizacion,
    ErrorNormalizacion,
    PasoDesconocidoError,
    TextoVacioError,
)
from .normalizador import NormalizadorDeTexto
from .segmentador import segmentar

__all__ = [
    "clasificar_fragmento",
    "clasificar_fragmentos",
    "ErrorEnPasoDeNormalizacion",
    "ErrorNormalizacion",
    "NormalizadorDeTexto",
    "PasoDesconocidoError",
    "TextoVacioError",
    "segmentar",
]
