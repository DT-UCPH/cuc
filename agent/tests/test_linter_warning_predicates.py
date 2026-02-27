"""Unit tests for linter warning predicate helpers."""

import unittest

from linter.lint import (
    analysis_has_homonym_marked_n_clitic,
    analysis_has_invalid_enclitic_plus,
    analysis_has_lexeme_t_split_without_reconstructed_t,
    analysis_has_missing_feminine_singular_split,
    analysis_has_missing_lexeme_m_before_plural_split,
    analysis_has_missing_plural_split,
    analysis_has_missing_suffix_plus,
    choose_lookup_candidates,
    missing_required_n_assimilation_marker,
    missing_required_verb_stem_markers,
    required_verb_stem_markers_from_pos,
    row_has_ambiguous_l_in_offering_sequence,
    row_has_baal_labourer_in_ktu1,
    row_has_baal_verbal_missing_slash,
    row_has_mixed_baal_dn_labourer_reading,
    variant_has_baad_plus_n,
    variant_has_lexeme_terminal_single_suffix_split,
    variant_has_suffix_payload_linked_dulat,
    verb_root_lookup_keys,
)


class LinterWarningPredicateTest(unittest.TestCase):
    def test_lexeme_t_split_without_reconstructed_t_detected(self) -> None:
        self.assertTrue(analysis_has_lexeme_t_split_without_reconstructed_t("thm/t"))

    def test_lexeme_t_split_with_reconstructed_t_not_flagged(self) -> None:
        self.assertFalse(analysis_has_lexeme_t_split_without_reconstructed_t("thm(t/t"))

    def test_feminine_singular_missing_split_detected(self) -> None:
        self.assertTrue(analysis_has_missing_feminine_singular_split("mlkt/", "mlkt"))

    def test_feminine_singular_split_not_flagged_once_split(self) -> None:
        self.assertFalse(analysis_has_missing_feminine_singular_split("mlk/t", "mlkt"))

    def test_plural_missing_split_detected_for_lemma_style(self) -> None:
        self.assertTrue(analysis_has_missing_plural_split("il(I)/", "ilm"))

    def test_plural_not_flagged_for_singular_t_lemma(self) -> None:
        self.assertFalse(analysis_has_missing_plural_split("dqt(I)/", "dqt"))

    def test_missing_lexeme_m_before_plural_split_detected(self) -> None:
        self.assertTrue(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="šm(I)/m",
                surface="šmm",
                declared_lemma="šmm",
            )
        )
        self.assertTrue(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="šmm(I)/m",
                surface="šmm",
                declared_lemma="šmm",
            )
        )
        self.assertTrue(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="pnm/+h",
                surface="pnh",
                declared_lemma="pnm",
            )
        )
        self.assertTrue(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="pn/m",
                surface="pn",
                declared_lemma="pnm",
            )
        )

    def test_lexeme_m_before_plural_split_not_flagged_when_present(self) -> None:
        self.assertFalse(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="šm(m(I)/m",
                surface="šmm",
                declared_lemma="šmm",
            )
        )
        self.assertFalse(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="šlm(II)/m",
                surface="šlmm",
                declared_lemma="šlm",
            )
        )
        self.assertFalse(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="pn(m/+h",
                surface="pnh",
                declared_lemma="pnm",
            )
        )
        self.assertFalse(
            analysis_has_missing_lexeme_m_before_plural_split(
                analysis="pn(m/",
                surface="pn",
                declared_lemma="pnm",
            )
        )

    def test_suffix_missing_plus_detected_for_reconstructed_base(self) -> None:
        self.assertTrue(analysis_has_missing_suffix_plus("l(I)", "ln"))

    def test_suffix_missing_plus_detected_for_explicit_suffix_letters(self) -> None:
        self.assertTrue(analysis_has_missing_suffix_plus("npšh/", "npšh"))

    def test_suffix_not_flagged_without_suffix_shape(self) -> None:
        self.assertFalse(analysis_has_missing_suffix_plus("ˤl(I)", "ˤl"))

    def test_suffix_not_flagged_for_enclitic_tilde_encoding(self) -> None:
        self.assertFalse(analysis_has_missing_suffix_plus("mṣd(III)/~h", "mṣdh"))

    def test_required_verb_markers_from_pos(self) -> None:
        self.assertEqual(required_verb_stem_markers_from_pos("vb D"), {":d"})
        self.assertEqual(required_verb_stem_markers_from_pos("vb Lt"), {":l"})
        self.assertEqual(required_verb_stem_markers_from_pos("vb R"), {":r"})
        self.assertEqual(required_verb_stem_markers_from_pos("vb Gpass"), {":pass"})
        self.assertEqual(required_verb_stem_markers_from_pos("vb D/L"), {":d", ":l"})
        self.assertEqual(required_verb_stem_markers_from_pos("vb. n. D"), set())

    def test_missing_required_verb_markers_detected(self) -> None:
        self.assertEqual(missing_required_verb_stem_markers("kbd[", "vb D"), [":d"])
        self.assertEqual(missing_required_verb_stem_markers("!y!knn[+h", "vb L"), [":l"])
        self.assertEqual(missing_required_verb_stem_markers("qtl[:pass", "vb Gpass"), [])
        self.assertEqual(missing_required_verb_stem_markers("ktl/", "vb D"), [])

    def test_missing_required_n_assimilation_marker_detected(self) -> None:
        self.assertTrue(missing_required_n_assimilation_marker("!t!ṯbr[", "vb N"))
        self.assertFalse(missing_required_n_assimilation_marker("!t!](n]ṯbr[", "vb N"))
        self.assertFalse(missing_required_n_assimilation_marker("!t!nṯbr[", "vb N"))
        self.assertFalse(missing_required_n_assimilation_marker("!t!ṯbr[", "vb G"))

    def test_verb_root_lookup_keys_include_non_slash_variant(self) -> None:
        keys = verb_root_lookup_keys("dk")
        self.assertIn("/d-k/", keys)
        self.assertIn("d-k/", keys)

    def test_choose_lookup_candidates_prefers_lexeme_then_surface(self) -> None:
        picked, mode = choose_lookup_candidates("ydk", [1], [2])
        self.assertEqual(mode, "lexeme")
        self.assertEqual(picked, [1])

        picked, mode = choose_lookup_candidates("ydk", [], [2])
        self.assertEqual(mode, "surface-fallback")
        self.assertEqual(picked, [2])

        picked, mode = choose_lookup_candidates("", [], [3])
        self.assertEqual(mode, "surface")
        self.assertEqual(picked, [3])

    def test_enclitic_plus_is_invalid(self) -> None:
        self.assertTrue(analysis_has_invalid_enclitic_plus("bˤd~+n"))
        self.assertFalse(analysis_has_invalid_enclitic_plus("bˤd~n"))

    def test_homonym_marked_suffix_or_enclitic_is_invalid(self) -> None:
        self.assertTrue(analysis_has_homonym_marked_n_clitic("ˤl(I)+n(I)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("!t!ṣḥ[+n(II)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("x~n(III)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("[n(IV)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("bt(II)/+h(I)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("d+k(II)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("bn(I)/+ny(III)="))

    def test_plain_suffix_or_enclitic_not_flagged(self) -> None:
        self.assertFalse(analysis_has_homonym_marked_n_clitic("ˤl(I)+n"))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("ˤl(I)+n="))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("x~n"))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("[n"))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("bt(II)/+h="))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("d+k"))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("bn(I)/+ny"))

    def test_lexeme_final_n_split_detected(self) -> None:
        self.assertTrue(variant_has_lexeme_terminal_single_suffix_split("mṯ/+n", "mṯn"))
        self.assertTrue(variant_has_lexeme_terminal_single_suffix_split("lš/+n", "lšn"))
        self.assertFalse(variant_has_lexeme_terminal_single_suffix_split("bn(I)/+ny", "bn (I)"))

    def test_explicit_suffix_token_not_flagged(self) -> None:
        self.assertFalse(
            variant_has_lexeme_terminal_single_suffix_split("ḥr(I)/+n(I)", "ḥr (I),-n (I)")
        )

    def test_baad_enclitic_plus_detected(self) -> None:
        self.assertTrue(variant_has_baad_plus_n("bˤd+n", "bʕd"))
        self.assertFalse(variant_has_baad_plus_n("ˤl(I)+n", "ʕl (I)"))

    def test_suffix_payload_linked_dulat_detected(self) -> None:
        self.assertTrue(variant_has_suffix_payload_linked_dulat("g/+h", "g, -h (I)"))
        self.assertTrue(variant_has_suffix_payload_linked_dulat("!y!ṣḥ[+n", "/ṣ-ḥ/, -n (II)"))
        self.assertFalse(variant_has_suffix_payload_linked_dulat("g/", "g, -h (I)"))
        self.assertFalse(variant_has_suffix_payload_linked_dulat("g/+h", "g"))

    def test_baal_mixed_dn_labourer_detected(self) -> None:
        self.assertTrue(
            row_has_mixed_baal_dn_labourer_reading(
                surface="bˤlm",
                analysis_field="bˤl(II)/;bˤl(I)/m",
                dulat_field="bʕl (II);bʕl (I)",
                pos_field="n. m./DN;n. m.",
                gloss_field="Baʿlu;labourer",
            )
        )

    def test_baal_single_plural_lord_not_flagged(self) -> None:
        self.assertFalse(
            row_has_mixed_baal_dn_labourer_reading(
                surface="bˤlm",
                analysis_field="bˤl(II)/m",
                dulat_field="bʕl (II)",
                pos_field="n. m.",
                gloss_field="lord",
            )
        )

    def test_offering_sequence_l_ambiguity_detected(self) -> None:
        self.assertTrue(
            row_has_ambiguous_l_in_offering_sequence(
                surface="l",
                analysis_field="l(I);l(II);l(III)",
                pos_field="prep.;adv.;functor",
                prev_surface="gdlt",
                prev_pos="n. f.",
                next_pos="DN",
            )
        )

    def test_non_offering_l_ambiguity_not_detected(self) -> None:
        self.assertFalse(
            row_has_ambiguous_l_in_offering_sequence(
                surface="l",
                analysis_field="l(I);l(II);l(III)",
                pos_field="prep.;adv.;functor",
                prev_surface="ḥẓr",
                prev_pos="n. m.",
                next_pos="n. f.",
            )
        )

    def test_baal_labourer_forbidden_in_ktu1(self) -> None:
        self.assertTrue(
            row_has_baal_labourer_in_ktu1(
                file_path="out/KTU 1.105.tsv",
                surface="bˤl",
                analysis_field="bˤl(II)/;bˤl(I)/;bˤl[/",
                dulat_field="bʕl (II);bʕl (I);/b-ʕ-l/",
                pos_field="n. m./DN;n. m.;vb",
                gloss_field="Baʿlu;labourer;to make",
            )
        )

    def test_baal_labourer_allowed_outside_ktu1(self) -> None:
        self.assertFalse(
            row_has_baal_labourer_in_ktu1(
                file_path="out/KTU 4.1.tsv",
                surface="bˤl",
                analysis_field="bˤl(II)/;bˤl(I)/;bˤl[/",
                dulat_field="bʕl (II);bʕl (I);/b-ʕ-l/",
                pos_field="n. m./DN;n. m.;vb",
                gloss_field="Baʿlu;labourer;to make",
            )
        )

    def test_baal_verbal_missing_slash_detected(self) -> None:
        self.assertTrue(
            row_has_baal_verbal_missing_slash(
                analysis_field="bˤl(II)/;bˤl[",
                dulat_field="bʕl (II);/b-ʕ-l/",
            )
        )

    def test_baal_verbal_with_slash_not_flagged(self) -> None:
        self.assertFalse(
            row_has_baal_verbal_missing_slash(
                analysis_field="bˤl(II)/;bˤl[/",
                dulat_field="bʕl (II);/b-ʕ-l/",
            )
        )


if __name__ == "__main__":
    unittest.main()
