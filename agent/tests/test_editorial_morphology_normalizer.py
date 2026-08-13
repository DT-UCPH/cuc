"""Tests for morphology over the edited rather than physical sign sequence."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.editorial_morphology_normalizer import (
    EditorialMorphologyNormalizer,
    normalize_analysis_to_edited_reading,
)


class EditorialMorphologyNormalizerTest(unittest.TestCase):
    def test_drops_erased_surface_only_letter(self) -> None:
        self.assertEqual(
            normalize_analysis_to_edited_reading("g&mpn(III)/", "gpn"),
            "gpn(III)/",
        )

    def test_keeps_lexical_allographic_substitution(self) -> None:
        self.assertEqual(
            normalize_analysis_to_edited_reading("(ṯ&tydr/", "tydr"),
            "(ṯ&tydr/",
        )

    def test_refuses_to_delete_a_lexical_letter(self) -> None:
        self.assertIsNone(normalize_analysis_to_edited_reading("gmpn(III)/", "gpn"))

    def test_row_uses_internal_edited_reading_target(self) -> None:
        row = TabletRow(
            line_id="158634",
            surface="gmpn",
            analysis="g&mpn(III)/",
            dulat="gpn (III)",
            pos="DN m.",
            gloss="Gapnu",
            comment="Edited reading: gpn",
        )
        fixed = EditorialMorphologyNormalizer().refine_row(row)
        self.assertEqual(fixed.analysis, "gpn(III)/")
        self.assertEqual(fixed.surface, "gmpn")


if __name__ == "__main__":
    unittest.main()
