"""Normalizacion, segmentacion y senales NLP."""

from .clasificador import clasificar_fragmento, clasificar_fragmentos
from .detector_ambiguedades import (
    detectar_ambiguedades_y_terminos_vagos,
    detectar_en_fragmentos,
)
from .errores import (
    ErrorEnPasoDeNormalizacion,
    ErrorNormalizacion,
    ErrorProcesamientoNLP,
    ModeloNLPNoDisponibleError,
    PasoDesconocidoError,
    TextoVacioError,
)
from .extractor_elementos import (
    extraer_actores_acciones_condiciones,
    extraer_de_fragmentos,
)
from .normalizador import NormalizadorDeTexto
from .pipeline import analizar_texto
from .segmentador import segmentar

__all__ = [
    "analizar_texto",
    "clasificar_fragmento",
    "clasificar_fragmentos",
    "detectar_ambiguedades_y_terminos_vagos",
    "detectar_en_fragmentos",
    "ErrorEnPasoDeNormalizacion",
    "ErrorNormalizacion",
    "ErrorProcesamientoNLP",
    "extraer_actores_acciones_condiciones",
    "extraer_de_fragmentos",
    "ModeloNLPNoDisponibleError",
    "NormalizadorDeTexto",
    "PasoDesconocidoError",
    "TextoVacioError",
    "segmentar",
]
