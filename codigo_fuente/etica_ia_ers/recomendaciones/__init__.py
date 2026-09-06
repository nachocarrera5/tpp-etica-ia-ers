"""Alertas y recomendaciones de mejora documental."""

from .errores import (
    ErrorGeneracionRecomendaciones,
    ResultadosIncompatiblesError,
)
from .generador import generar_alertas_y_recomendaciones

__all__ = [
    "ErrorGeneracionRecomendaciones",
    "ResultadosIncompatiblesError",
    "generar_alertas_y_recomendaciones",
]
