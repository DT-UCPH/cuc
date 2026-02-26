"""Tests for TN directional/enclitic -h normalization to '~h'."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.toponym_directional_h import ToponymDirectionalHFixer


class _MorphGate:
    def __init__(self, mapping=None) -> None:
        self.mapping = dict(mapping or {})

    def surface_morphologies(self, token: str, surface: str) -> set[str]:
        return set(self.mapping.get((token, surface), set()))


class ToponymDirectionalHFixerTest(unittest.TestCase):
    def test_rewrites_tn_suffix_h_to_enclitic_marker(self) -> None:
        gate = _MorphGate({("mṣd (III)", "mṣdh"): {"sg., suff."}})
        fixer = ToponymDirectionalHFixer(gate=gate)
        row = TabletRow("1", "mṣdh", "mṣd(III)/", "mṣd (III)", "TN", "mṣd", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "mṣd(III)/~h")

    def test_keeps_non_toponym_unchanged(self) -> None:
        gate = _MorphGate({("npš", "npšh"): {"suff."}})
        fixer = ToponymDirectionalHFixer(gate=gate)
        row = TabletRow("2", "npšh", "npš/", "npš", "n. f.", "throat", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "npš/")


if __name__ == "__main__":
    unittest.main()
