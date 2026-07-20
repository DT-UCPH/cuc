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

    def test_restores_single_missing_tail_letter_for_nominal_variant(self) -> None:
        row = TabletRow("14", "ˤnn", "ˤn(I)/", "ʕn (I)", "n. f. du.", "eye", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ˤn(I)&n/")

    def test_restores_single_missing_tail_letter_for_pronoun_variant(self) -> None:
        row = TabletRow("15", "atm", "at(I)", "ảt (I)", "pers. pn.", "you", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "at(I)&m")

    def test_restores_nominal_t_suffix_from_surface(self) -> None:
        row = TabletRow("16", "arbˤt", "arbˤ/", "ảrbʕ", "num.", "four", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "arbˤ/t")

    def test_restores_assimilated_n_to_t_nominal_suffix(self) -> None:
        row = TabletRow("17", "ṯt", "ṯn(I)/", "ṯn (I)", "num. f.", "two", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ṯ(n(I)/t")

    def test_restores_plain_nominal_m_suffix(self) -> None:
        row = TabletRow("18", "ṯnm", "ṯn(I)", "ṯn (I)", "num.", "two", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ṯn(I)/m")

    def test_restores_surface_host_before_m_suffix(self) -> None:
        row = TabletRow("19", "bhtm", "bt(II)/", "bt (II)", "n. m. pl.", "house", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bht(II)/m")

    def test_restores_hidden_weak_y_before_enclitic_m(self) -> None:
        row = TabletRow("20", "ṯnm", "ṯny[~m", "/ṯ-n-y/", "vb G impv. 2", "to repeat", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ṯn(y[~m")

    def test_restores_missing_y_before_plus_m(self) -> None:
        row = TabletRow("21", "bym", "b+m(I)", "b", "prep.", "in", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "b&y+m(I)")

    def test_restores_case_vowel_tail_for_ksi(self) -> None:
        row = TabletRow("22", "ksi", "ks/", "ks/śủ", "n. f.", "seat", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ks&i/")

    def test_rewrites_tmthetn_to_gt_prefixed_with_energic_n(self) -> None:
        row = TabletRow("23", "tmtḫṣn", "mḫṣ[ḫṣn", "/m-ḫ-ṣ/", "vb G prefc.", "to wound", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!m]t]ḫṣ[~n")
        self.assertEqual(result.pos, "vb Gt prefc. 3 f. sg.")

    def test_restores_hidden_weak_y_before_suffix_t(self) -> None:
        row = TabletRow("24", "klt", "kly[t", "/k-l-y/", "vb G suffc. 1 c. sg.", "to finish", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "kl(y[t")


if __name__ == "__main__":
    unittest.main()
