"""Rubrica e indicadores agregados de cobertura documental."""

from __future__ import annotations

from .calculador import (
    DIMENSIONES_POR_GRUPO,
    GRUPO_POR_DIMENSION,
    NOMBRES_DIMENSION,
    UMBRAL_EXPLICITO_PONDERADO,
    calcular_cobertura_etica,
)
from .errores import (
    ErrorRubricaYAgregacion,
    ResultadoEvaluacionInvalidoError,
)

__all__ = [
    "DIMENSIONES_POR_GRUPO",
    "ErrorRubricaYAgregacion",
    "GRUPO_POR_DIMENSION",
    "NOMBRES_DIMENSION",
    "ResultadoEvaluacionInvalidoError",
    "UMBRAL_EXPLICITO_PONDERADO",
    "calcular_cobertura_etica",
]
