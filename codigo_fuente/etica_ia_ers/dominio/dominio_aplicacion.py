"""Dominios de aplicacion con guardrails especificos."""

from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import Any, Optional


class DominioAplicacion(str, Enum):
    CREDITICIO = "crediticio"
    SALUD = "salud"
    EMPLEO = "empleo"
    EDUCACION = "educacion"
    SECTOR_PUBLICO = "sector_publico"
    RECOMENDACION = "recomendacion"


# Variantes con las que la interfaz, la API y el corpus de validacion declaran
# cada dominio. Se comparan normalizadas y completas, nunca por subcadena, para
# que un dominio libre como "Logistica de salud animal" no active Salud.
_ALIAS_DOMINIO = {
    DominioAplicacion.CREDITICIO: (
        "crediticio",
        "credito",
        "credito y finanzas",
        "finanzas",
        "financiero",
        "banca",
        "bancario",
        "scoring crediticio",
    ),
    DominioAplicacion.SALUD: (
        "salud",
        "sanitario",
        "medico",
        "medicina",
        "clinico",
        "diagnostico medico",
    ),
    DominioAplicacion.EMPLEO: (
        "empleo",
        "laboral",
        "trabajo",
        "recursos humanos",
        "rrhh",
        "seleccion de personal",
    ),
    DominioAplicacion.EDUCACION: (
        "educacion",
        "educativo",
        "academico",
        "ensenanza",
    ),
    DominioAplicacion.SECTOR_PUBLICO: (
        "sector publico",
        "administracion publica",
        "gobierno",
        "publico",
    ),
    DominioAplicacion.RECOMENDACION: (
        "recomendacion",
        "recomendacion y contenidos",
        "recomendador",
        "sistema recomendador",
        "contenidos",
    ),
}


def _normalizar_dominio(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto.casefold())
    sin_acentos = "".join(
        caracter
        for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"[\s_-]+", " ", sin_acentos).strip()


_DOMINIO_POR_ALIAS = {
    _normalizar_dominio(alias): dominio
    for dominio, alias_dominio in _ALIAS_DOMINIO.items()
    for alias in alias_dominio
}


def resolver_dominio_aplicacion(valor: Any) -> Optional[DominioAplicacion]:
    """Traduce el dominio declarado en los metadatos a un dominio conocido."""
    if isinstance(valor, DominioAplicacion):
        return valor
    if not isinstance(valor, str):
        return None
    return _DOMINIO_POR_ALIAS.get(_normalizar_dominio(valor))
