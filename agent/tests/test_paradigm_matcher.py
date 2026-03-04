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

    def test_generates_all_visible_t_suffix_candidates_for_strong_g_root(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ypˤt",
            dulat="/y-p-ʕ/",
            stem="G",
            conjugation="suffc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("ypˤ[t===", "3", "f.", "sg."), rendered)
        self.assertIn(("ypˤ[t=", "2", "m.", "sg."), rendered)
        self.assertIn(("ypˤ[t==", "2", "f.", "sg."), rendered)
        self.assertIn(("ypˤ[t", "1", "c.", "sg."), rendered)

    def test_generates_all_visible_t_suffix_candidates_for_n_stem(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ypˤt",
            dulat="/y-p-ʕ/",
            stem="N",
            conjugation="suffc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("(]n]ypˤ[t===", "3", "f.", "sg."), rendered)
        self.assertIn(("(]n]ypˤ[t=", "2", "m.", "sg."), rendered)
        self.assertIn(("(]n]ypˤ[t==", "2", "f.", "sg."), rendered)
        self.assertIn(("(]n]ypˤ[t", "1", "c.", "sg."), rendered)

    def test_generates_weak_final_d_prefix_candidates_when_pattern_table_is_sparse(self) -> None:
        candidates = generate_verbal_candidates(
            surface="tkly",
            dulat="/k-l-y/",
            stem="D",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!t=!kly[:d", "2", "m.", "sg."), rendered)

    def test_generates_dt_prefix_candidates_for_weak_final_roots(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ttrp",
            dulat="/r-p-y/",
            stem="Dt",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!t!]t]rp(y[:d", "3", "m.", "du."), rendered)
        self.assertIn(("!t!]t]rp(y[:d:w", "3", "m.", "pl."), rendered)

    def test_generates_weak_initial_prefix_candidates(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ytn",
            dulat="/y-t-n/",
            stem="G",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!y!(ytn[", "3", "m.", "sg."), rendered)


if __name__ == "__main__":
    unittest.main()
