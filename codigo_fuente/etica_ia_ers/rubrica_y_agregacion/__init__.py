"""Rubrica e indicadores agregados de cobertura documental."""

from .calculador import calcular_cobertura_etica
from .errores import (
    ErrorRubricaYAgregacion,
    ResultadoEvaluacionInvalidoError,
)

__all__ = [
    "ErrorRubricaYAgregacion",
    "ResultadoEvaluacionInvalidoError",
    "calcular_cobertura_etica",
]
