"""Tests for morphology-aware nominal /y and /h case-ending splitting."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.nominal_case_ending_yh import NominalCaseEndingYHFixer


class _MorphGate:
    def __init__(self, mapping=None) -> None:
        self.mapping = dict(mapping or {})

    def surface_morphologies(self, token: str, surface: str) -> set[str]:
        return set(self.mapping.get((token, surface), set()))


class NominalCaseEndingYHFixerTest(unittest.TestCase):
    def test_splits_umy_into_um_y(self) -> None:
        gate = _MorphGate({("ủm", "umy"): {"sg."}})
        fixer = NominalCaseEndingYHFixer(gate=gate)
        row = TabletRow("1", "umy", "umy/", "ủm", "n. f.", "mother", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "um/y")

    def test_adds_missing_y_split_when_surface_has_y(self) -> None:
        gate = _MorphGate({("hkl", "hkly"): {"sg."}})
        fixer = NominalCaseEndingYHFixer(gate=gate)
        row = TabletRow("2", "hkly", "hkl/", "hkl", "n. m.", "palace", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hkl/y")

    def test_keeps_suffixal_forms_unchanged(self) -> None:
        gate = _MorphGate({("bt (II)", "bty"): {"suff."}})
        fixer = NominalCaseEndingYHFixer(gate=gate)
        row = TabletRow("3", "bty", "bty/", "bt (II)", "n. m.", "house", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "bty/")

    def test_non_nominal_pos_unchanged(self) -> None:
        gate = _MorphGate({("ủm", "umy"): {"sg."}})
        fixer = NominalCaseEndingYHFixer(gate=gate)
        row = TabletRow("4", "umy", "umy/", "ủm", "prep.", "to", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "umy/")


if __name__ == "__main__":
    unittest.main()
