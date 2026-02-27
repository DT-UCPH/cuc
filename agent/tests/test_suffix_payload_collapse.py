"""Tests for collapsing suffix-linked DULAT/POS/gloss payload."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.suffix_payload_collapse import SuffixPayloadCollapseFixer


class SuffixPayloadCollapseFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = SuffixPayloadCollapseFixer()

    def test_collapses_single_variant_suffix_payload(self) -> None:
        row = TabletRow(
            "1",
            "gh",
            "g/+h",
            "g, -h (I)",
            "n. m., pers. pn.",
            "(loud) voice, his /her",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.dulat, "g")
        self.assertEqual(result.pos, "n. m.")
        self.assertEqual(result.gloss, "(loud) voice")

    def test_preserves_internal_commas_in_base_gloss(self) -> None:
        row = TabletRow(
            "2",
            "ttnk",
            "!t!(ytn[+k",
            "/y-t-n/, -k (I)",
            "vb, pers. pn./morph.",
            "to give, hand over, grant, bestow, your(s)",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.dulat, "/y-t-n/")
        self.assertEqual(result.pos, "vb")
        self.assertEqual(result.gloss, "to give, hand over, grant, bestow")

    def test_does_not_change_when_dulat_has_no_suffix_payload(self) -> None:
        row = TabletRow("3", "gh", "g/+h", "g", "n. m.", "(loud) voice", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.dulat, "g")
        self.assertEqual(result.pos, "n. m.")
        self.assertEqual(result.gloss, "(loud) voice")

    def test_collapses_only_aligned_variant(self) -> None:
        row = TabletRow(
            "4",
            "x",
            "g/+h; g/",
            "g, -h (I); g",
            "n. m., pers. pn.; n. m.",
            "(loud) voice, his /her; (loud) voice",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.dulat, "g; g")
        self.assertEqual(result.pos, "n. m.; n. m.")
        self.assertEqual(result.gloss, "(loud) voice; (loud) voice")


if __name__ == "__main__":
    unittest.main()
