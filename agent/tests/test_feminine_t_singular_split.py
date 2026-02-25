"""Tests for feminine singular noun split refinement."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.base import TabletRow
from pipeline.steps.feminine_t_singular_split import FeminineTSingularSplitFixer


class _PluralOnlyGate:
    def __init__(self, plural_tokens=None, morphologies=None) -> None:
        self._plural = set(plural_tokens or [])
        self._morphologies = dict(morphologies or {})

    def is_plural_token(self, token: str, surface: str = "") -> bool:
        return token in self._plural

    def surface_morphologies(self, token: str, surface: str) -> set[str]:
        return set(self._morphologies.get((token, surface), set()))


class FeminineTSingularSplitFixerTest(unittest.TestCase):
    def test_splits_feminine_noun_without_homonym(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("1", "mlkt", "mlkt/", "mlkt", "n. f.", "queen", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "mlk(t/t")

    def test_splits_feminine_dn_with_homonym(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            feminine_onomastic_tokens={"ảṯrt (II)"},
        )
        row = TabletRow(
            "2",
            "aṯrt",
            "aṯrt(II)/",
            "ảṯrt (II)",
            "DN",
            "ʾAṯiratu",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "aṯr(t(II)/t")

    def test_splits_feminine_dn_with_homonym_for_anat(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            feminine_onomastic_tokens={"ʕnt (I)"},
        )
        row = TabletRow(
            "3",
            "ˤnt",
            "ˤnt(I)/",
            "ʕnt (I)",
            "DN",
            "ʿAnatu",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ˤn(t(I)/t")

    def test_keeps_masculine_dn_unchanged(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            feminine_onomastic_tokens={"ʕnt (I)"},
        )
        row = TabletRow("4", "ym", "ym/", "ym", "DN", "Yammu", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ym/")

    def test_keeps_plural_forms_for_plural_gate_tokens(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            gate=_PluralOnlyGate(plural_tokens={"kṯr (I)"}),
        )
        row = TabletRow("5", "kṯrt", "kṯrt(I)/", "kṯr (I)", "n. f.", "Kothar", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "kṯrt(I)/")

    def test_reads_feminine_onomastic_from_three_column_override_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            overrides_path = Path(tmp_dir) / "onomastic.tsv"
            overrides_path.write_text(
                "dulat\tPOS\tgloss\nảṯrt (II)\tDN f.\tʾAṯiratu/Athirat\nbʕl (II)\tDN m.\tBaʿlu\n",
                encoding="utf-8",
            )
            fixer = FeminineTSingularSplitFixer(overrides_path=overrides_path)
            row = TabletRow(
                "6",
                "aṯrt",
                "aṯrt(II)/",
                "ảṯrt (II)",
                "DN",
                "Asherah",
                "",
            )
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "aṯr(t(II)/t")

    def test_rewrites_simple_t_split_when_lemma_is_t_final(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("7", "thmt", "thm/t", "thmt", "n. f.", "Primordial Ocean", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "thm(t/t")

    def test_rewrites_simple_t_split_and_appends_terminal_m(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("7b", "thmtm", "thm/t", "thmt", "n. f.", "Primordial Ocean", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "thm(t/tm")

    def test_rewrites_homonym_t_split_when_lemma_is_t_final(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("8", "bt", "b(I)/t", "bt (I)", "n. f.", "daughter", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "b(t(I)/t")

    def test_injects_homonym_from_dulat_when_missing_in_analysis(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("8b", "bt", "b/t", "bt (I)", "n. f.", "daughter", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "b(t(I)/t")

    def test_injects_homonym_and_appends_terminal_m(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("8c", "btm", "b/t", "bt (I)", "n. f.", "daughter", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "b(t(I)/tm")

    def test_keeps_simple_t_split_when_lemma_is_not_t_final(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("9", "kṯrt", "kṯr(I)/t", "kṯr (I)", "n. f.", "Kothar", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "kṯr(I)/t")

    def test_split_variant_still_gets_lexical_t_when_plural_gate_matches(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            gate=_PluralOnlyGate(plural_tokens={"bt (I)"}),
        )
        row = TabletRow("10", "bt", "b/t", "bt (I)", "n. f.", "daughter", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "b(t(I)/t")

    def test_rewrites_t_equal_split_when_lemma_is_t_final(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("11", "hmlt", "hml/t=", "hmlt", "n. f.", "multitude", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hml(t/t=")

    def test_promotes_t_split_to_t_equal_for_plurale_tantum_feminine_noun(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow(
            "12",
            "hmlt",
            "hml(t/t",
            "hmlt",
            "n. f. pl. tant.?",
            "multitude",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hml(t/t=")

    def test_rewrites_unsplit_lexical_t_forced_plural_token_to_t_equal(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow(
            "13",
            "ṯnt",
            "ṯnt(II)/",
            "ṯnt (II)",
            "n. f.",
            "urine",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ṯn(t(II)/t=")

    def test_rewrites_split_lexical_t_forced_plural_token_to_t_equal(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow(
            "14",
            "ṯnt",
            "ṯn(t(II)/t",
            "ṯnt (II)",
            "n. f.",
            "urine",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ṯn(t(II)/t=")

    def test_adds_feminine_t_split_from_dulat_surface_morphology(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            gate=_PluralOnlyGate(morphologies={("pḥl", "pḥlt"): {"f."}}),
        )
        row = TabletRow("15", "pḥlt", "pḥl/", "pḥl", "n. m.", "ass", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pḥl/t")

    def test_splits_t_final_noun_for_generic_noun_pos(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("16", "hwt", "hwt(I)/", "hwt (I)", "n.", "word", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hw(t(I)/t")

    def test_keeps_t_final_noun_with_explicit_masculine_pos(self) -> None:
        fixer = FeminineTSingularSplitFixer()
        row = TabletRow("17", "hwt", "hwt(I)/", "hwt (I)", "n. m.", "word", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hwt(I)/")

    def test_emits_singular_and_plural_t_variants_for_sg_pl_ambiguous_surface(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            gate=_PluralOnlyGate(
                morphologies={
                    ("ṣrrt", "ṣrrt"): {"sg.", "pl."},
                }
            ),
        )
        row = TabletRow("18", "ṣrrt", "ṣrrt/", "ṣrrt", "n. f.", "height(s)", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ṣrr(t/t;ṣrr(t/t=")

    def test_splits_t_final_numeral_without_adding_plural_pair(self) -> None:
        fixer = FeminineTSingularSplitFixer(
            gate=_PluralOnlyGate(
                plural_tokens={"rb(b)t"},
                morphologies={
                    ("rb(b)t", "rbt"): {"sg.", "pl."},
                },
            ),
        )
        row = TabletRow("19", "rbt", "rbt/", "rb(b)t", "num.", "ten thousand", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "rb(t/t")


if __name__ == "__main__":
    unittest.main()
