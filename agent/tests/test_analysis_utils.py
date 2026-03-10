"""Tests for analysis/surface reconstruction helpers."""

import unittest

from pipeline.steps.analysis_utils import reconstruct_surface_from_analysis


class AnalysisUtilsTest(unittest.TestCase):
    def test_reconstruction_keeps_suffix_t_after_stem_marker(self) -> None:
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt==="), "šlmt")
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt="), "šlmt")
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt=="), "šlmt")
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:dt"), "šlmt")

    def test_reconstruction_keeps_suffix_w_after_stem_marker(self) -> None:
        self.assertEqual(reconstruct_surface_from_analysis("šlm[:d:w"), "šlmw")


if __name__ == "__main__":
    unittest.main()
