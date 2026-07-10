from __future__ import annotations

import unittest
from pathlib import Path

from etica_ia_ers.configuration.loader import load_analysis_config, load_guardrail


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def test_load_default_analysis_config(self) -> None:
        config = load_analysis_config(PROJECT_ROOT / "config" / "analysis.default.json")

        self.assertEqual(config.codigo, "default-es")
        self.assertEqual(config.version, 1)
        self.assertEqual(config.idioma, "es")
        self.assertTrue(config.activa)

    def test_load_guardrail(self) -> None:
        guardrail = load_guardrail(PROJECT_ROOT / "config" / "guardrails" / "GR-D01-DELIM-USOS.v1.json")

        self.assertEqual(guardrail.codigo, "GR-D01-DELIM-USOS")
        self.assertEqual(guardrail.version, 1)
        self.assertEqual(guardrail.dimensiones[0]["codigo"], "D01")


if __name__ == "__main__":
    unittest.main()

