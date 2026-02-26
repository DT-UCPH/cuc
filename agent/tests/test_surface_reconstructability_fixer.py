"""Tests for known surface reconstructability normalization rules."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.surface_reconstructability_fixer import SurfaceReconstructabilityFixer


class SurfaceReconstructabilityFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = SurfaceReconstructabilityFixer()

    def test_expands_thmt_to_dual_lexeme_options(self) -> None:
        row = TabletRow("1", "thmt", "thmt/", "thmt", "n. f.", "Primordial Ocean", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "thm(t/t; thm/t")
        self.assertEqual(result.dulat, "thmt; thm")
        self.assertEqual(result.pos, "n. f.; n. m.")
        self.assertEqual(result.gloss, "Primordial Ocean; ocean/deep")

    def test_normalizes_thmtm_and_drops_pos_dual_marker(self) -> None:
        row = TabletRow("2", "thmtm", "thmt/m", "thmt", "n. f. du.", "Primordial Ocean", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "thm(t/tm")
        self.assertEqual(result.pos, "n. f.")

    def test_repairs_mtm_variants_to_reconstruct_surface(self) -> None:
        row = TabletRow(
            "3",
            "mtm",
            "mt(II)/; mt[; mt(I)/t=",
            "mt (II); /m-t/; mt (I)",
            "n. m.; vb; n. m.",
            "death; to die; dead person",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "mt(II)/~m; mt[~m; mt(I)/m")

    def test_repairs_bnwth_plural_feminine_allograph(self) -> None:
        row = TabletRow("4", "bnwth", "bn(t(II)/t=", "bnt (II)", "n. f.", "produce", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bn&w(t(II)/t=+h")

    def test_repairs_ymy_plural_allograph(self) -> None:
        row = TabletRow("5", "ymy", "ym(I)/m", "ym (I)", "n. m.", "day", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ym(I)&y/")

    def test_repairs_ymt_nominal_variant_only(self) -> None:
        row = TabletRow(
            "6",
            "ymt",
            "ym(I)/m; !y!mt[",
            "ym (I); /m-t/",
            "n. m.; vb",
            "day; to die",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ym(I)/t=; !y!mt[")

    def test_repairs_ymm_nominal_variant_only(self) -> None:
        row = TabletRow(
            "7",
            "ymm",
            "ym(I)/; ym(II)/",
            "ym (I); ym (II)",
            "n. m.; n. m.",
            "day; sea",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ym(I)/m; ym(II)/")

    def test_repairs_ilh_variant_of_ilt_with_surface_h(self) -> None:
        row = TabletRow(
            "8",
            "ilh",
            "il(t(I)/t=; ilh/",
            "ỉlt (I); ỉlh",
            "n. f.; DN",
            "goddess; the ‘Divine One’",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "il(t(I)/&h; ilh/")

    def test_repairs_ilht_variant_of_ilt_with_surface_ht(self) -> None:
        row = TabletRow("9", "ilht", "il(t(I)/t=", "ỉlt (I)", "n. f.", "goddess", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "il(t(I)/&ht")

    def test_downgrades_athat_ambiguous_t_equal_to_t(self) -> None:
        row = TabletRow("10", "aṯt", "aṯ(t/t=", "ảṯt", "n. f.", "woman", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "aṯ(t/t")

    def test_downgrades_that_ambiguous_t_equal_to_t(self) -> None:
        row = TabletRow("11", "ṯat", "ṯa(t/t=", "ṯảt", "n. f.", "ewe", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ṯa(t/t")

    def test_removes_spurious_non_prefixed_stem_tail(self) -> None:
        row = TabletRow("12", "šqrb", "]š]qrb[b", "/q-r-b/", "vb Š", "to approach", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "]š]qrb[")

    def test_keeps_prefixed_forms_unchanged_for_tail_rule(self) -> None:
        row = TabletRow("13", "yšlḥm", "!y!]š]lḥm(I)[", "/l-ḥ-m/", "vb Š", "to fight", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!]š]lḥm(I)[")


if __name__ == "__main__":
    unittest.main()
