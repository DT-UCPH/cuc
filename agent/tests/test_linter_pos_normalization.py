"""Tests for POS normalization in DULAT validation."""

import unittest

from linter.lint import normalize_pos_option_for_validation, split_pos_options


class LinterPosNormalizationTest(unittest.TestCase):
    def test_strips_nominal_number_markers_for_validation(self) -> None:
        self.assertEqual(normalize_pos_option_for_validation("n. m. du."), "n")
        self.assertEqual(normalize_pos_option_for_validation("n. f. pl."), "n")
        self.assertEqual(normalize_pos_option_for_validation("adj. f. sg."), "adj.")

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


if __name__ == "__main__":
    unittest.main()
