"""Tests for plurale-tantum -m noun normalization refinement."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.plurale_tantum_m import PluraleTantumMFixer


class _PluraleTantumGate:
    def __init__(self, plural_tokens=None, plurale_tantum_tokens=None) -> None:
        self._plural = set(plural_tokens or [])
        self._pl_tant = set(plurale_tantum_tokens or [])

    def is_plural_token(self, token: str, surface: str = "") -> bool:
        return token in self._plural

    def is_plurale_tantum_noun_token(self, token: str) -> bool:
        return token in self._pl_tant


class PluraleTantumMFixerTest(unittest.TestCase):
    def test_rewrites_missing_lexeme_m_before_plural_split(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"šmm (I)"},
                plurale_tantum_tokens={"šmm (I)"},
            )
        )
        row = TabletRow("1", "šmm", "šm(I)/m", "šmm (I)", "n. m.", "heavens", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šm(m(I)/m")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_rewrites_unsplit_variant_for_terminal_m_lemma(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"šmm (I)"},
                plurale_tantum_tokens={"šmm (I)"},
            )
        )
        row = TabletRow("2", "šmm", "šmm(I)/", "šmm (I)", "n. m.", "heavens", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šm(m(I)/m")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_injects_allograph_y_for_shmym(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"šmm (I)"},
                plurale_tantum_tokens={"šmm (I)"},
            )
        )
        row = TabletRow("3", "šmym", "šm(I)/m", "šmm (I)", "n. m.", "heavens", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šm&y(m(I)/m")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_rewrites_suffix_form_with_terminal_m_base(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"šmm (I)"},
                plurale_tantum_tokens={"šmm (I)"},
            )
        )
        row = TabletRow("4", "šmmh", "šmm(I)/+h", "šmm (I)", "n. m.", "heavens", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šm(m(I)/m+h")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_drops_spurious_nm_suffix_before_terminal_m_rewrite(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"pnm"},
                plurale_tantum_tokens={"pnm"},
            )
        )
        row = TabletRow("5", "pnm", "pn/m+nm", "pnm", "n. m.", "face", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pn(m/m")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_marks_only_targeted_pos_variant_in_multi_variant_row(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"pnm"},
                plurale_tantum_tokens={"pnm"},
            )
        )
        row = TabletRow(
            "6",
            "pn",
            "pn/m; pn",
            "pnm; pn",
            "n. m.; functor",
            "face; lest",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pn(m/; pn")
        self.assertEqual(result.pos, "n. m. pl. tant.; functor")

    def test_rewrites_suffix_variant_when_host_surface_drops_terminal_m(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"pnm"},
                plurale_tantum_tokens={"pnm"},
            )
        )
        row = TabletRow("6b", "pnh", "pnm/+h", "pnm", "n. m.", "face", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pn(m/+h")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_infers_suffix_h_for_pnh_when_missing(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"pnm"},
                plurale_tantum_tokens={"pnm"},
            )
        )
        row = TabletRow("6c", "pnh", "pnm/", "pnm", "n. m.", "face", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pn(m/+h")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_infers_suffix_y_for_pny_when_missing(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"pnm"},
                plurale_tantum_tokens={"pnm"},
            )
        )
        row = TabletRow("6d", "pny", "pnm/", "pnm", "n. m.", "face", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pn(m/+y")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_normalizes_plus_ny_tail_when_single_y_matches_surface(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"pnm"},
                plurale_tantum_tokens={"pnm"},
            )
        )
        row = TabletRow("6e", "pny", "pnm/+ny", "pnm", "n. m.", "face", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pn(m/+y")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_infers_suffix_k_from_split_m_row(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"ḥym"},
                plurale_tantum_tokens={"ḥym"},
            )
        )
        row = TabletRow("6f", "ḥyk", "ḥy/m", "ḥym", "n. m.", "life", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ḥy(m/+k")
        self.assertEqual(result.pos, "n. m. pl. tant.")

    def test_keeps_non_target_lemma_unchanged(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"šlm (II)"},
                plurale_tantum_tokens=set(),
            )
        )
        row = TabletRow(
            "7",
            "šlmm",
            "šlm(II)/m",
            "šlm (II)",
            "n. m.",
            "communion victim / sacrifice",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šlm(II)/m")
        self.assertEqual(result.pos, "n. m.")

    def test_repairs_false_positive_plurale_tantum_for_shlm(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"šlm (II)"},
                plurale_tantum_tokens=set(),
            )
        )
        row = TabletRow(
            "7b",
            "šlmm",
            "šl(m(II)/m~m; šlm(II)/m",
            "šlm (II); šlm (II)",
            "n. m. pl. tant.; n. m. pl. tant.",
            "communion victim / sacrifice; communion victim / sacrifice",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šlm(II)/~m; šlm(II)/m")
        self.assertEqual(result.pos, "n. m.; n. m.")

    def test_repairs_false_positive_plurale_tantum_for_qm(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"qm"},
                plurale_tantum_tokens=set(),
            )
        )
        row = TabletRow(
            "7c",
            "qm",
            "qm[; q(m/m",
            "/q-m/; qm",
            "vb; n. m. pl. tant.",
            "to stand up; adversary",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "qm[; qm/")
        self.assertEqual(result.pos, "vb; n. m.")

    def test_repairs_false_positive_plurale_tantum_for_hlm(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"ḥlm (II)"},
                plurale_tantum_tokens=set(),
            )
        )
        row = TabletRow(
            "7d",
            "ḥlmm",
            "ḥl(II)/m",
            "ḥlm (II)",
            "n. m. pl. tant.",
            "growing animal",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ḥlm(II)/m")
        self.assertEqual(result.pos, "n. m.")

    def test_strips_false_positive_plurale_tantum_marker_without_analysis_repair(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"ḥlm (II)"},
                plurale_tantum_tokens=set(),
            )
        )
        row = TabletRow(
            "7e",
            "ḥlmm",
            "ḥlm(II)/m",
            "ḥlm (II)",
            "n. m. pl. tant.",
            "growing animal",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ḥlm(II)/m")
        self.assertEqual(result.pos, "n. m.")

    def test_does_not_add_pl_tant_for_non_m_lemma_even_if_gate_flags_it(self) -> None:
        fixer = PluraleTantumMFixer(
            gate=_PluraleTantumGate(
                plural_tokens={"pʕn"},
                plurale_tantum_tokens={"pʕn"},
            )
        )
        row = TabletRow("8", "pˤnk", "pˤn/+k", "pʕn", "n. f.", "foot", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "pˤn/+k")
        self.assertEqual(result.pos, "n. f.")


if __name__ == "__main__":
    unittest.main()
