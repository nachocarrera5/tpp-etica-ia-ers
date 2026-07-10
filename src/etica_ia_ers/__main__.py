from __future__ import annotations

from pathlib import Path

from etica_ia_ers.configuration.loader import load_analysis_config, load_guardrail


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    analysis_config = load_analysis_config(project_root / "config" / "analysis.default.json")
    guardrail = load_guardrail(project_root / "config" / "guardrails" / "GR-D01-DELIM-USOS.v1.json")

    print(f"Configuracion: {analysis_config.codigo} v{analysis_config.version}")
    print(f"Guardrail ejemplo: {guardrail.codigo} v{guardrail.version}")


if __name__ == "__main__":
    main()
