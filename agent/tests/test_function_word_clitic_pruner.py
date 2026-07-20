"""Tests for pruning duplicate host-only function-word rows with clitic siblings."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.function_word_clitic_pruner import FunctionWordCliticPruner


class FunctionWordCliticPrunerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pruner = FunctionWordCliticPruner()

    def test_drops_bare_prep_when_same_lexeme_has_clitic_variant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "tablet.tsv"
            path.write_text(
                "# KTU 1.103 I:1\n"
                "1\tbh\tb\tb\tprep.\tin\t\n"
                "1\tbh\tb+h\tb\tprep.\tin\t\n"
                "1\tbh\tnqb[\t/n-q-b/\tvb\tto pierce\t\n",
                encoding="utf-8",
            )

            result = self.pruner.refine_file(path)
            lines = path.read_text(encoding="utf-8").splitlines()

            self.assertEqual(result.rows_changed, 1)
            self.assertNotIn("1\tbh\tb\tb\tprep.\tin\t", lines)
            self.assertIn("1\tbh\tb+h\tb\tprep.\tin\t", lines)
            self.assertIn("1\tbh\tnqb[\t/n-q-b/\tvb\tto pierce\t", lines)

    def test_keeps_host_row_when_clitic_sibling_has_different_lexeme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "tablet.tsv"
            path.write_text(
                "1\tbh\tb\tb\tprep.\tin\t\n1\tbh\tg+h\tg\tn. m. sg.\t(loud) voice\t\n",
                encoding="utf-8",
            )

            result = self.pruner.refine_file(path)
            lines = path.read_text(encoding="utf-8").splitlines()

            self.assertEqual(result.rows_changed, 0)
            self.assertIn("1\tbh\tb\tb\tprep.\tin\t", lines)
            self.assertIn("1\tbh\tg+h\tg\tn. m. sg.\t(loud) voice\t", lines)


if __name__ == "__main__":
    unittest.main()
