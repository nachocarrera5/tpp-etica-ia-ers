"""Entidad de dominio para el resultado de normalización."""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class TextoNormalizado:
    """Resultado de la normalización de un texto de ERS.

    Attributes:
        original: Texto original tal como fue recibido.
        normalizado: Texto después de aplicar los pasos de normalización.
        pasos_aplicados: Lista ordenada de nombres de pasos aplicados.
    """

    original: str
    normalizado: str
    pasos_aplicados: List[str] = field(default_factory=list)
