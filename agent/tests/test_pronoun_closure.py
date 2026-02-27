"""Tests for pronoun closure normalization (no trailing '/')."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.pronoun_closure import PronounClosureFixer


class PronounClosureFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = PronounClosureFixer()

    def test_removes_slash_from_personal_pronoun(self) -> None:
        row = TabletRow("1", "hw", "hw/", "hw", "pers. pn.", "he, it", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "hw")

    def test_preserves_homonym_marker_when_removing_slash(self) -> None:
        row = TabletRow("2", "hm", "hm(II)/", "hm (II)", "pers. pn.", "them", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "hm(II)")

    def test_keeps_noun_with_slash_unchanged(self) -> None:
        row = TabletRow("3", "hw", "hw/", "hw", "n. m.", "something", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "hw/")

    def test_rewrites_only_pronoun_variant(self) -> None:
        row = TabletRow(
            "4",
            "xy",
            "hw/; bʕl(II)/",
            "hw; bʕl (II)",
            "pers. pn.; n. m./DN",
            "he; Baʿlu",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "hw; bʕl(II)/")


if __name__ == "__main__":
    unittest.main()
