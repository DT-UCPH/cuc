"""Tests for deterministic verbal completion."""

import unittest
from pathlib import Path

from morph_features.dulat_feature_reader import DulatFeatureReader
from morph_features.verbal_completion import VerbalFeatureCompleter, rewrite_row
from pipeline.steps.base import TabletRow
from pipeline.steps.verbal_feature_completion import VerbalFeatureCompletionFixer


class _FakeReader(DulatFeatureReader):
    def __init__(self, mapping=None):
        self.mapping = dict(mapping or {})
        super().__init__(db_path=Path("unused.sqlite"))

    def read_surface_features(self, surface: str, dulat: str, pos: str = ""):
        if (surface, dulat) in self.mapping:
            return self.mapping[(surface, dulat)]
        return super().read_surface_features(surface, dulat, pos)


class _Features:
    def __init__(self, forms):
        self.morphologies = tuple()
        self.forms = tuple(forms)
        self.genders = tuple()
        self.numbers = tuple()
        self.states = tuple()
        self.cases = tuple()


class VerbalFeatureCompletionTest(unittest.TestCase):
    def test_rewrites_explicit_second_masculine_prefix(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("tmḫṣ", "/m-ḫ-ṣ/"): _Features(("prefc",))})
        )
        row = TabletRow("139770", "tmḫṣ", "!t=!mḫṣ[", "/m-ḫ-ṣ/", "vb G prefc.", "to wound", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "vb G prefc. 2 m. sg.")

    def test_splits_prefc_and_suffc_rows(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("yṯb", "/y-ṯ-b/"): _Features(("prefc", "suffc"))})
        )
        row = TabletRow(
            "139808", "yṯb", "!y!(yṯb[", "/y-ṯ-b/", "vb G prefc. / vb G suffc.", "to sit down", ""
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.analysis, "!y!(yṯb[; yṯb[")
        self.assertEqual(rewritten.pos, "vb G prefc. 3 m. sg.; vb G suffc. 3 m. sg.")

    def test_preserves_participle_and_adds_default_gender_number(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("yṯb", "/y-ṯ-b/"): _Features(("act", "ptc"))})
        )
        row = TabletRow("139808", "yṯb", "yṯb[/", "/y-ṯ-b/", "vb G act. ptcpl.", "to sit down", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "vb G act. ptcpl. m. sg.")

    def test_pipeline_step_uses_real_dulat_reader(self) -> None:
        fixer = VerbalFeatureCompletionFixer(Path("unused.sqlite"))
        row = TabletRow("1", "mlk", "mlk/", "mlk", "n. m.", "king", "")
        self.assertEqual(fixer.refine_row(row), row)


if __name__ == "__main__":
    unittest.main()
