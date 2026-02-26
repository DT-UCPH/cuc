"""Tests for suffix/enclitic paradigm normalization in col3 analysis."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.suffix_paradigm_normalizer import SuffixParadigmNormalizer


class SuffixParadigmNormalizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = SuffixParadigmNormalizer()

    def test_strips_homonym_tags_from_suffix_markers(self) -> None:
        row = TabletRow(
            "1",
            "x",
            "ḥr(I)/+n(I); ap(I)+h(II); š/+ny(III); !t!ṣḥ[+n(III); x~n(IV); y[n(II)=",
            "a; b; c; d; e; f",
            "n.; n.; n.; vb; n.; vb",
            "a; b; c; d; e; f",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(
            result.analysis,
            "ḥr(I)/+n; ap(I)+h; š/+ny; !t!ṣḥ[+n; x~n; y[n=",
        )

    def test_keeps_non_pronominal_m_variants_unchanged(self) -> None:
        row = TabletRow("2", "x", "lt+m(I); w+m(II)", "a; b", "n.; conj.", "a; b", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "lt+m(I); w+m(II)")

    def test_keeps_canonical_suffix_markers_unchanged(self) -> None:
        row = TabletRow(
            "3",
            "x",
            "ˤl(I)+n; bt(II)/+h=; bn(I)/+ny; x~n; y[n=",
            "a; b; c; d; e",
            "prep.; n.; n.; n.; vb",
            "a; b; c; d; e",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ˤl(I)+n; bt(II)/+h=; bn(I)/+ny; x~n; y[n=")


if __name__ == "__main__":
    unittest.main()
