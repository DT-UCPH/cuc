"""Tests for analysis/surface reconstruction helpers."""

import unittest

from pipeline.steps.analysis_utils import (
    analysis_matches_surface,
    reconstruct_surface_from_analysis,
)


class AnalysisUtilsTest(unittest.TestCase):
    def test_reconstruction_keeps_suffix_t_after_stem_marker(self) -> None:
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt==="), "šlmt")
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt="), "šlmt")
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt=="), "šlmt")
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt"), "šlmt")

    def test_reconstruction_keeps_suffix_w_after_stem_marker(self) -> None:
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:d:w"), "šlmw")

    def test_surface_match_accepts_hidden_plural_w(self) -> None:
        self.assertTrue(analysis_matches_surface("tṯkḥ", "!t!ṯkḥ[:w"))
        self.assertTrue(analysis_matches_surface("tṯbr", "!t!(]n]ṯbr[:w"))
        self.assertTrue(analysis_matches_surface("šn", "šn(w[:w"))

    def test_surface_match_rejects_non_matching_suffix_letters(self) -> None:
        self.assertFalse(analysis_matches_surface("šlm", "šlm[:d:t"))


if __name__ == "__main__":
    unittest.main()
