"""Tests for morphology.py-backed verbal candidate generation."""

import unittest

from morph_features.paradigm_matcher import generate_verbal_candidates


class ParadigmMatcherTest(unittest.TestCase):
    def test_generates_plural_and_dual_prefix_candidates_for_strong_g_root(self) -> None:
        candidates = generate_verbal_candidates(
            surface="tṯkḥ",
            dulat="/ṯ-k-ḥ/",
            stem="G",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!t!ṯkḥ[", "3", "f.", "sg."), rendered)
        self.assertIn(("!t!ṯkḥ[", "3", "m.", "du."), rendered)
        self.assertIn(("!t!ṯkḥ[:w", "3", "m.", "pl."), rendered)

    def test_generates_plural_suffix_candidate_when_surface_supports_it(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ytn",
            dulat="/y-t-n/",
            stem="G",
            conjugation="suffc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("ytn[", "3", "m.", "sg."), rendered)
        self.assertIn(("ytn[:w", "3", "m.", "pl."), rendered)


if __name__ == "__main__":
    unittest.main()
