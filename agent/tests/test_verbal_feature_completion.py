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

    def test_constrains_explicit_forms_with_dulat_form_metadata(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("ynaṣn", "/n-ʔ-ṣ/"): _Features(("prefc.",))})
        )
        row = TabletRow(
            "135906",
            "ynaṣn",
            "!y!n(ʔ&aṣ[n",
            "/n-ʔ-ṣ/",
            "vb G prefc. / vb G suffc.",
            "to despise",
            "",
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.analysis, "!y!n(ʔ&aṣ[n")
        self.assertEqual(rewritten.pos, "vb G prefc. 3 m. sg.")

    def test_replaces_non_overlapping_explicit_form_with_dulat_form_metadata(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("ynaṣn", "/n-ʔ-ṣ/"): _Features(("prefc.",))})
        )
        row = TabletRow(
            "135906",
            "ynaṣn",
            "ynaṣn[",
            "/n-ʔ-ṣ/",
            "vb G suffc.",
            "to despise",
            "",
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.analysis, "ynaṣn[")
        self.assertEqual(rewritten.pos, "vb G prefc.")

    def test_preserves_participle_and_adds_default_gender_number(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("yṯb", "/y-ṯ-b/"): _Features(("act", "ptc"))})
        )
        row = TabletRow("139808", "yṯb", "yṯb[/", "/y-ṯ-b/", "vb G act. ptcpl.", "to sit down", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "vb G act. ptcpl. m. sg. abs. nom.")

    def test_marks_suffix_bearing_participle_as_construct(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("bˤl", "/b-ʕ-l/"): _Features(("act", "ptc"))})
        )
        row = TabletRow("151368", "bˤlh", "bˤl[/+h", "/b-ʕ-l/", "vb G act. ptcpl.", "to make", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "vb G act. ptcpl. m. sg. cstr. nom.")

    def test_pipeline_step_uses_real_dulat_reader(self) -> None:
        fixer = VerbalFeatureCompletionFixer(Path("unused.sqlite"))
        row = TabletRow("1", "mlk", "mlk/", "mlk", "n. m.", "king", "")
        self.assertEqual(fixer.refine_row(row), row)

    def test_uses_pattern_candidates_when_analysis_lacks_explicit_png(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("tṯkḥ", "/ṯ-k-ḥ/"): _Features(("prefc",))})
        )
        row = TabletRow("139782", "tṯkḥ", "!t!ṯkḥ[", "/ṯ-k-ḥ/", "vb G prefc.", "to burn", "")
        rewritten = rewrite_row(row, completer)
        self.assertIn("vb G prefc. 3 f. sg.", rewritten.pos)
        self.assertIn("vb G prefc. 3 m. du.", rewritten.pos)
        self.assertIn("vb G prefc. 3 m. pl.", rewritten.pos)

    def test_expands_under_specified_suffix_analysis_from_surface(self) -> None:
        completer = VerbalFeatureCompleter(
            _FakeReader({("ypˤt", "/y-p-ʕ/"): _Features(("suffc",))})
        )
        row = TabletRow("136034", "ypˤt", "ypˤt[", "/y-p-ʕ/", "vb G suffc.", "to go up", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.analysis, "ypˤ[t===; ypˤ[t=; ypˤ[t==; ypˤ[t")
        self.assertEqual(
            rewritten.pos,
            (
                "vb G suffc. 3 f. sg.; vb G suffc. 2 m. sg.; "
                "vb G suffc. 2 f. sg.; vb G suffc. 1 c. sg."
            ),
        )

    def test_suffix_fallback_marks_visible_nonlexeme_prefix_for_g_stem(self) -> None:
        completer = VerbalFeatureCompleter(_FakeReader({("nˤr", "/ʕ-r/"): _Features(("suffc",))}))
        row = TabletRow(
            "152967",
            "nˤr",
            "!n!(]n]ˤr[",
            "/ʕ-r/",
            "vb G suffc.",
            "to become agitated",
            "",
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.analysis, "&nˤr[")
        self.assertEqual(rewritten.pos, "vb G suffc. 3 m. sg.")

    def test_suffix_fallback_keeps_visible_n_marker_for_n_stem(self) -> None:
        completer = VerbalFeatureCompleter(_FakeReader({("nˤr", "/ʕ-r/"): _Features(("suffc",))}))
        row = TabletRow(
            "152967",
            "nˤr",
            "!n!(]n]ˤr[",
            "/ʕ-r/",
            "vb N suffc.",
            "to become agitated",
            "",
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.analysis, "]n]ˤr[")
        self.assertEqual(rewritten.pos, "vb N suffc. 3 m. sg.")


if __name__ == "__main__":
    unittest.main()
