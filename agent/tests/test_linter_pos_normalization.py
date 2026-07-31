"""Tests for POS normalization in DULAT validation."""

import unittest

from linter.lint import (
    normalize_pos_option_for_validation,
    pos_option_matches_allowed,
    split_pos_options,
)


class LinterPosNormalizationTest(unittest.TestCase):
    def test_strips_nominal_number_markers_for_validation(self) -> None:
        self.assertEqual(normalize_pos_option_for_validation("n. m. du."), "n")
        self.assertEqual(normalize_pos_option_for_validation("n. f. pl."), "n")
        self.assertEqual(normalize_pos_option_for_validation("adj. f. sg."), "adj.")

    def test_strips_state_and_case_markers_for_validation(self) -> None:
        self.assertEqual(normalize_pos_option_for_validation("n. m. sg. cstr. nom."), "n")
        self.assertEqual(normalize_pos_option_for_validation("n. f. pl. abs. gen."), "n")
        self.assertEqual(
            normalize_pos_option_for_validation("DN m. sg. abs. nom."),
            "dn",
        )

    def test_strips_functor_qualifier_for_validation(self) -> None:
        self.assertEqual(normalize_pos_option_for_validation("prep. functor"), "prep.")

    def test_strips_attached_affix_tail_for_validation(self) -> None:
        """Clitics/suffixes are affix morphology, not POS-head information."""
        self.assertEqual(
            normalize_pos_option_for_validation("n. m. sg. abs. nom + encl. -m"), "n"
        )
        self.assertEqual(
            normalize_pos_option_for_validation("n. f. du. cstr. gen. + 3 f. sg. suff."), "n"
        )
        self.assertEqual(
            normalize_pos_option_for_validation("prep. + 2 m. sg. suff."), "prep."
        )
        self.assertEqual(
            normalize_pos_option_for_validation("DN m. sg. abs. gen. + encl. -m"), "dn"
        )

    def test_strips_directional_morphology_before_validating_noun_head(self) -> None:
        self.assertEqual(
            normalize_pos_option_for_validation("n. f. sg. abs. acc. + dir. -h"), "n"
        )

    def test_normalizes_personal_pronoun_terminal_punctuation(self) -> None:
        self.assertEqual(normalize_pos_option_for_validation("pers. pn."), "pers. pn")
        self.assertTrue(pos_option_matches_allowed("pers. pn.", {"pers. pn"}))

    def test_affix_bearing_option_matches_coarse_dulat_label(self) -> None:
        self.assertTrue(pos_option_matches_allowed("n. m. sg. abs. nom + encl. -m", {"n"}))
        self.assertTrue(
            pos_option_matches_allowed("prep. + 3 m. sg. suff.", {"prep."})
        )
        # A genuinely wrong head must still fail once the tail is removed.
        self.assertFalse(pos_option_matches_allowed("vb G suffc. 3 m. sg.", {"n"}))

    def test_splits_spaced_slash_pos_options(self) -> None:
        self.assertEqual(
            split_pos_options("n. m. pl. / n. m. du."),
            ["n. m. pl.", "n. m. du."],
        )

    def test_keeps_known_slash_labels_as_single_option(self) -> None:
        self.assertEqual(
            split_pos_options("det. / rel. functor"),
            ["det. or rel. functor"],
        )

    def test_composite_or_label_matches_component_allowlist(self) -> None:
        allowed = {"adv.", "prep."}
        self.assertTrue(pos_option_matches_allowed("adv. or prep.", allowed))

    def test_enriched_adj_option_matches_composite_allowed_label(self) -> None:
        allowed = {"adj. or n"}
        self.assertTrue(
            pos_option_matches_allowed("adj. m. sg. abs. nom.", allowed),
        )
        self.assertTrue(
            pos_option_matches_allowed("adj. f. pl. abs. nom.", allowed),
        )


if __name__ == "__main__":
    unittest.main()
