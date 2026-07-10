from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from etica_ia_ers.domain import AnalysisConfig, Guardrail


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_analysis_config(path: str | Path) -> AnalysisConfig:
    raw = _read_json(Path(path))
    return AnalysisConfig(
        codigo=raw["codigo"],
        version=int(raw["version"]),
        idioma=raw.get("idioma", "es"),
        parametros=raw.get("parametros", {}),
        activa=bool(raw.get("activa", True)),
    )


def load_guardrail(path: str | Path) -> Guardrail:
    raw = _read_json(Path(path))
    return Guardrail(
        codigo=raw["codigo"],
        nombre=raw["nombre"],
        version=int(raw["version"]),
        estado=raw["estado"],
        familia=raw["familia"],
        descripcion=raw["descripcion"],
        dimensiones=raw["dimensiones"],
        criterios=raw.get("criterios", []),
        marcos_referencia=raw.get("marcos_referencia", []),
        aplicabilidad=raw.get("aplicabilidad", {}),
        evidencia_esperada=raw.get("evidencia_esperada", {}),
        senales=raw.get("senales", {}),
        clasificacion=raw.get("clasificacion", {}),
        prioridad=raw.get("prioridad", {}),
        revision_humana=raw.get("revision_humana", {}),
        recomendacion=raw.get("recomendacion", {}),
        salida=raw.get("salida", {}),
    )

