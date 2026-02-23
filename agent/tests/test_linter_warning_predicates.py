"""Unit tests for linter warning predicate helpers."""

import unittest

from linter.lint import (
    analysis_has_homonym_marked_n_clitic,
    analysis_has_invalid_enclitic_plus,
    analysis_has_lexeme_t_split_without_reconstructed_t,
    analysis_has_missing_feminine_singular_split,
    analysis_has_missing_plural_split,
    analysis_has_missing_suffix_plus,
    choose_lookup_candidates,
    row_has_ambiguous_l_in_offering_sequence,
    row_has_baal_labourer_in_ktu1,
    row_has_mixed_baal_dn_labourer_reading,
    variant_has_baad_plus_n,
    variant_has_lexeme_terminal_single_suffix_split,
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

    def test_suffix_missing_plus_detected_for_reconstructed_base(self) -> None:
        self.assertTrue(analysis_has_missing_suffix_plus("l(I)", "ln"))

    def test_suffix_missing_plus_detected_for_explicit_suffix_letters(self) -> None:
        self.assertTrue(analysis_has_missing_suffix_plus("npšh/", "npšh"))

    def test_suffix_not_flagged_without_suffix_shape(self) -> None:
        self.assertFalse(analysis_has_missing_suffix_plus("ˤl(I)", "ˤl"))

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

    def test_homonym_marked_enclitic_n_is_invalid(self) -> None:
        self.assertTrue(analysis_has_homonym_marked_n_clitic("ˤl(I)+n(I)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("!t!ṣḥ[+n(II)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("x~n(III)"))
        self.assertTrue(analysis_has_homonym_marked_n_clitic("[n(IV)"))

    def test_plain_enclitic_n_not_flagged(self) -> None:
        self.assertFalse(analysis_has_homonym_marked_n_clitic("ˤl(I)+n"))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("ˤl(I)+n="))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("x~n"))
        self.assertFalse(analysis_has_homonym_marked_n_clitic("[n"))

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
                analysis_field="bˤl(II)/;bˤl(I)/;bˤl[",
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
                analysis_field="bˤl(II)/;bˤl(I)/;bˤl[",
                dulat_field="bʕl (II);bʕl (I);/b-ʕ-l/",
                pos_field="n. m./DN;n. m.;vb",
                gloss_field="Baʿlu;labourer;to make",
            )
        )


if __name__ == "__main__":
    unittest.main()
