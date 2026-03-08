"""Tests for canonical clitic notation on function-word analyses."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.function_word_clitic_notation import FunctionWordCliticNotationFixer


class FunctionWordCliticNotationFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = FunctionWordCliticNotationFixer()

    def test_rewrites_prep_m_suffix_to_plus_marker(self) -> None:
        row = TabletRow("1", "lm", "l(I)&m", "l (I)", "prep.", "to", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "l(I)+m(I)")

    def test_rewrites_prep_enclitic_m_tail_to_pronominal_plus(self) -> None:
        row = TabletRow("2", "ˤlm", "ˤl(I)&~m", "ʕl (I)", "prep.", "upon", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ˤl(I)+m(I)")

    def test_rewrites_prep_t_suffix_to_plus_marker(self) -> None:
        row = TabletRow("3", "ˤlt", "ˤl(I)&t", "ʕl (I)", "prep.", "upon", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ˤl(I)+t")

    def test_collapses_split_hm_tail_to_combined_suffix(self) -> None:
        row = TabletRow("4", "bhm", "b&h+m(I)", "b", "prep.", "in", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "b+hm")

    def test_preserves_hidden_weak_y_before_suffix(self) -> None:
        row = TabletRow("5", "bym", "b&y+m(I)", "b", "prep.", "in", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "b&y+m(I)")

    def test_skips_non_function_word_rows(self) -> None:
        row = TabletRow("6", "atm", "at(I)&m", "ảt (I)", "pers. pn.", "you", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "at(I)&m")


if __name__ == "__main__":
    unittest.main()
