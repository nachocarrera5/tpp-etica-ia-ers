"""Normalizacion, segmentacion y senales NLP."""

from .clasificador import clasificar_fragmento, clasificar_fragmentos
from .errores import (
    ErrorEnPasoDeNormalizacion,
    ErrorNormalizacion,
    PasoDesconocidoError,
    TextoVacioError,
)
from .normalizador import NormalizadorDeTexto
from .pipeline import analizar_texto
from .segmentador import segmentar

__all__ = [
    "analizar_texto",
    "clasificar_fragmento",
    "clasificar_fragmentos",
    "ErrorEnPasoDeNormalizacion",
    "ErrorNormalizacion",
    "NormalizadorDeTexto",
    "PasoDesconocidoError",
    "TextoVacioError",
    "segmentar",
]
