"""Tests for feminine singular noun split refinement."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.base import TabletRow
from pipeline.steps.feminine_t_singular_split import FeminineTSingularSplitFixer


class _PluralOnlyGate:
    def __init__(self, plural_tokens=None) -> None:
        self._plural = set(plural_tokens or [])

    def is_plural_token(self, token: str, surface: str = "") -> bool:
        return token in self._plural


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


if __name__ == "__main__":
    unittest.main()
