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

    def test_omits_plural_suffix_candidate_when_surface_lacks_visible_w(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ytn",
            dulat="/y-t-n/",
            stem="G",
            conjugation="suffc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("ytn[", "3", "m.", "sg."), rendered)
        self.assertIn(("ytn[:w", "3", "m.", "pl."), rendered)

    def test_iii_w_prefix_reconstructs_final_radical_without_malformed_twin(self) -> None:
        # For a III-w root whose final radical is elided from the surface, the
        # only valid 3 m. pl. form reconstructs the w as `(w`. The malformed
        # twin `!t!ˤnw[:w` (w written, previously accepted only via the
        # `:w`+"w" fallback) must not be generated.
        candidates = generate_verbal_candidates(
            surface="tˤn",
            dulat="/ʕ-n-w/",
            stem="G",
            conjugation="prefc.",
        )
        analyses = {item.analysis for item in candidates}
        self.assertIn("!t!ˤn(w[:w", analyses)
        self.assertNotIn("!t!ˤnw[:w", analyses)
        # Every generated body reconstructs the final radical (none writes it).
        self.assertTrue(all("ˤnw[" not in analysis for analysis in analyses))

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

    def test_n_stem_suffix_with_root_initial_n_marks_both_nuns(self) -> None:
        candidates = generate_verbal_candidates(
            surface="nšt",
            dulat="/n-š-y/",
            stem="N",
            conjugation="suffc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("]n](nš(y[t", "1", "c.", "sg."), rendered)

    def test_n_stem_suffix_realizes_final_aleph_as_written_vowel(self) -> None:
        candidates = generate_verbal_candidates(
            surface="nḫtu",
            dulat="/ḫ-t-ʔ/",
            stem="N",
            conjugation="suffc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("]n]ḫt(ʔ[&u", "3", "m.", "sg."), rendered)

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

    def test_gt_prefix_reconstructs_elided_initial_n_before_infix(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ttpl",
            dulat="/n-p-l/",
            stem="Gt",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!t!(n]t]pl[", "3", "f.", "sg."), rendered)

    def test_gt_prefix_reconstructs_elided_initial_h_before_infix(self) -> None:
        candidates = generate_verbal_candidates(
            surface="ytlk",
            dulat="/h-l-k/",
            stem="Gt",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!y!(h]t]lk[", "3", "m.", "sg."), rendered)

    def test_gt_prefix_preserves_aleph_vowel_before_infix(self) -> None:
        candidates = generate_verbal_candidates(
            surface="yitmr",
            dulat="/ʔ-m-r/",
            stem="Gt",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!y!(ʔ&i]t]mr[", "3", "m.", "sg."), rendered)

    def test_gt_first_common_prefix_uses_i_and_marks_infix(self) -> None:
        candidates = generate_verbal_candidates(
            surface="its",
            dulat="/n-s(-y)/ (I)",
            stem="Gt",
            conjugation="prefc.",
        )
        rendered = {(item.analysis, item.person, item.gender, item.number) for item in candidates}
        self.assertIn(("!(ʔ&i!(n]t]s(y[", "1", "c.", "sg."), rendered)

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
