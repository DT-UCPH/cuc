"""Tests for canonical POS rendering from structured feature bundles."""

import unittest

from linter.lint import normalize_pos_option_for_validation
from morph_features.pos_renderer import render_pos
from morph_features.types import FeatureBundle


class PosRendererTest(unittest.TestCase):
    def test_number_alternatives_use_or_instead_of_pos_separator(self) -> None:
        bundle = FeatureBundle(
            part_of_speech="n.",
            gender="m.",
            number="pl. / du.",
            state="abs.",
            case="gen.",
        )
        self.assertEqual(render_pos(bundle), "n. m. pl. or du. abs. gen.")
        self.assertEqual(
            normalize_pos_option_for_validation(render_pos(bundle)),
            "n",
        )


if __name__ == "__main__":
    unittest.main()
