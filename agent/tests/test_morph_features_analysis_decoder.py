"""Tests for explicit parser analysis decoding."""

import unittest

from morph_features.analysis_decoder import (
    decode_analysis,
    explicit_prefix_features,
    explicit_suffix_conjugation_features,
)
from morph_features.non_vocalized_normalizer import normalize_vocalized_form


class AnalysisDecoderTest(unittest.TestCase):
    def test_decodes_explicit_prefix_markers(self) -> None:
        decoded = decode_analysis("!t=!qtl[")
        self.assertEqual(explicit_prefix_features(decoded), ("2", "m.", "sg."))

        decoded = decode_analysis("!t==!qtl[")
        self.assertEqual(explicit_prefix_features(decoded), ("2", "f.", "sg."))

        decoded = decode_analysis("!t===!qtl[")
        self.assertEqual(explicit_prefix_features(decoded), ("2", "m.", "pl."))

        decoded = decode_analysis("!y!qtl[")
        self.assertEqual(explicit_prefix_features(decoded), ("3", "m.", "sg."))

    def test_decodes_suffix_conjugation_markers(self) -> None:
        self.assertEqual(
            explicit_suffix_conjugation_features(decode_analysis("qtl[")), ("3", "m.", "sg.")
        )
        self.assertEqual(
            explicit_suffix_conjugation_features(decode_analysis("qtl[:w")), ("3", "m.", "pl.")
        )
        self.assertEqual(
            explicit_suffix_conjugation_features(decode_analysis("qtl[t=")), ("2", "m.", "sg.")
        )
        self.assertEqual(
            explicit_suffix_conjugation_features(decode_analysis("qtl[t==")), ("2", "f.", "sg.")
        )

    def test_marks_infinitive_and_participle(self) -> None:
        self.assertTrue(decode_analysis("!!rgm[/").is_infinitive)
        self.assertTrue(decode_analysis("rgm[/").is_participle)

    def test_normalizes_vocalized_forms(self) -> None:
        self.assertEqual(normalize_vocalized_form("/yaqtalu/"), "yqtl")
        self.assertEqual(normalize_vocalized_form("ảqtl"), "ʔqtl")


if __name__ == "__main__":
    unittest.main()
