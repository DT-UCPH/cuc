"""Tests for splitting mixed verb-form POS options by analysis encoding."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.verb_form_encoding_split import VerbFormEncodingSplitFixer


class VerbFormEncodingSplitFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = VerbFormEncodingSplitFixer()

    def test_splits_mixed_finite_and_nonfinite_options(self) -> None:
        row = TabletRow(
            "1",
            "rgm",
            "rgm[",
            "/r-g-m/",
            "vb G suffc. / vb G impv. / vb G inf. / vb G pass. ptcpl.",
            "to say",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "rgm[; !!rgm[/; rgm[/")
        self.assertEqual(result.dulat, "/r-g-m/; /r-g-m/; /r-g-m/")
        self.assertEqual(
            result.pos,
            "vb G suffc. / vb G impv.; vb G inf.; vb G pass. ptcpl.",
        )
        self.assertEqual(result.gloss, "to say; to say; to say")

    def test_promotes_single_nonfinite_option_to_nonfinite_encoding(self) -> None:
        row = TabletRow("2", "qtl", "qtl[", "/q-t-l/", "vb G inf.", "to kill", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!qtl[/")
        self.assertEqual(result.pos, "vb G inf.")

    def test_keeps_participle_as_nonfinite_without_infinitive_marker(self) -> None:
        row = TabletRow("5", "qtl", "!!qtl[/", "/q-t-l/", "vb G pass. ptcpl.", "killed", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "qtl[/")
        self.assertEqual(result.pos, "vb G pass. ptcpl.")

    def test_splits_prefixed_weak_form_into_canonical_nonfinite_variants(self) -> None:
        row = TabletRow(
            "6",
            "ydy",
            "!y!(ydy(I)[",
            "/y-d-y/ (I)",
            "vb G prefc. / vb G impv. / vb G inf. / vb G act. ptcpl. m.",
            "to throw",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!(ydy(I)[; !!ydy(I)[/; ydy(I)[/")
        self.assertEqual(
            result.pos,
            "vb G prefc. / vb G impv.; vb G inf.; vb G act. ptcpl. m.",
        )

    def test_rewrites_prefixed_infinitive_to_canonical_surface_form(self) -> None:
        row = TabletRow("7", "yld", "!y!(yld[", "/y-l-d/", "vb G inf.", "to give birth", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!yld[/")

    def test_rewrites_prefixed_participle_to_canonical_surface_form(self) -> None:
        row = TabletRow("8", "yṯb", "!y!(yṯb[", "/y-ṯ-b/", "vb G act. ptcpl.", "to sit", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "yṯb[/")

    def test_preserves_i_aleph_reconstruction_in_nonfinite_split(self) -> None:
        row = TabletRow(
            "9",
            "any",
            "!(ʔ&a!ny[",
            "/ʔ-n-y/",
            "vb G prefc. / vb G inf. / vb G ptcpl.",
            "to sigh",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!(ʔ&a!ny[; !!(ʔ&any[/; (ʔ&any[/")
        self.assertEqual(result.pos, "vb G prefc.; vb G inf.; vb G ptcpl.")

    def test_restores_i_aleph_on_full_surface_nonfinite_core(self) -> None:
        row = TabletRow("10", "aṯr", "aṯr[", "/ʔ-ṯ-r/", "vb G inf.", "to go", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!(ʔ&aṯr[/")

    def test_restores_missing_open_paren_for_i_aleph_participle(self) -> None:
        row = TabletRow(
            "11",
            "aklt",
            "ʔ&akl[t",
            "/ʔ-k-l/",
            "vb G act. ptcpl. m.",
            "to eat",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "(ʔ&akl[/t")

    def test_restores_i_aleph_participle_with_derived_mem_surface(self) -> None:
        row = TabletRow(
            "12",
            "maḫr",
            "ʔḫr[r",
            "/ʔ-ḫ-r/",
            "vb D ptcpl.",
            "to retain",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "(ʔ&aḫr[/")

    def test_restores_hidden_weak_final_radical_for_truncated_nonfinite_host(self) -> None:
        row = TabletRow("13", "bk", "bk[", "/b-k-y/", "vb G inf.", "to weep", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!bk(y[/")

    def test_demotes_single_finite_option_to_finite_encoding(self) -> None:
        row = TabletRow("3", "qtl", "!!qtl[/", "/q-t-l/", "vb G suffc.", "to kill", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "qtl[")
        self.assertEqual(result.pos, "vb G suffc.")

    def test_preserves_unprefixed_imperative_marker_for_finite_encoding(self) -> None:
        row = TabletRow("14", "qḥ", "!!(lqḥ[", "/l-q-ḥ/", "vb G impv. 2", "to get hold of", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!(lqḥ[")
        self.assertEqual(result.pos, "vb G impv. 2")

    def test_preserves_unprefixed_imperative_marker_in_mixed_form_row(self) -> None:
        row = TabletRow(
            "15",
            "qḥ",
            "!!(lqḥ[/",
            "/l-q-ḥ/",
            "vb G impv. 2 / vb G inf.",
            "to get hold of",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!(lqḥ[; !!(lqḥ[/")
        self.assertEqual(result.pos, "vb G impv. 2; vb G inf.")

    def test_nonverbal_row_unchanged(self) -> None:
        row = TabletRow("4", "mlk", "mlk/", "mlk", "n. m.", "king", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result, row)


if __name__ == "__main__":
    unittest.main()
