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


if __name__ == "__main__":
    unittest.main()
