"""Tests for splitting mixed verb-form POS options by analysis encoding."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.verb_form_encoding_split import VerbFormEncodingSplitFixer


class VerbFormEncodingSplitFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = VerbFormEncodingSplitFixer()

    def test_splits_mixed_finite_and_nonfinite_options(self) -> None:
        row = TabletRow(
            "1",
            "rgm",
            "rgm[",
            "/r-g-m/",
            "vb G suffc. / vb G impv. / vb G inf. / vb G pass. ptcpl.",
            "to say",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "rgm[; !!rgm[/; rgm[/")
        self.assertEqual(result.dulat, "/r-g-m/; /r-g-m/; /r-g-m/")
        self.assertEqual(
            result.pos,
            "vb G suffc. / vb G impv.; vb G inf.; vb G pass. ptcpl.",
        )
        self.assertEqual(result.gloss, "to say; to say; to say")

    def test_promotes_single_nonfinite_option_to_nonfinite_encoding(self) -> None:
        row = TabletRow("2", "qtl", "qtl[", "/q-t-l/", "vb G inf.", "to kill", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!qtl[/")
        self.assertEqual(result.pos, "vb G inf.")

    def test_keeps_participle_as_nonfinite_without_infinitive_marker(self) -> None:
        row = TabletRow("5", "qtl", "!!qtl[/", "/q-t-l/", "vb G pass. ptcpl.", "killed", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "qtl[/")
        self.assertEqual(result.pos, "vb G pass. ptcpl.")

    def test_demotes_single_finite_option_to_finite_encoding(self) -> None:
        row = TabletRow("3", "qtl", "!!qtl[/", "/q-t-l/", "vb G suffc.", "to kill", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "qtl[")
        self.assertEqual(result.pos, "vb G suffc.")

    def test_nonverbal_row_unchanged(self) -> None:
        row = TabletRow("4", "mlk", "mlk/", "mlk", "n. m.", "king", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result, row)


if __name__ == "__main__":
    unittest.main()
