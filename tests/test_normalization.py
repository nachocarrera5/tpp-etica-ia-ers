from __future__ import annotations

import unittest

from etica_ia_ers.processing.normalization import normalize_text


class NormalizationTests(unittest.TestCase):
    def test_normalize_spaces_and_blank_lines(self) -> None:
        raw = "  El sistema   debera revisar datos.\n\n\n\nDebe registrar responsable.  "

        normalized = normalize_text(raw)

        self.assertEqual(normalized, "El sistema debera revisar datos.\n\nDebe registrar responsable.")


if __name__ == "__main__":
    unittest.main()

