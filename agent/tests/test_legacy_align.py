from __future__ import annotations

import importlib.util
import io
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents"
    / "skills"
    / "review-automatic-parsing"
    / "scripts"
    / "legacy_align.py"
)
SPEC = importlib.util.spec_from_file_location("legacy_align", SCRIPT)
assert SPEC and SPEC.loader
legacy_align = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(legacy_align)


class LegacyAlignVerdictTests(unittest.TestCase):
    def test_csv_blank_id_continuation_is_preserved_as_alternative(self):
        rows = io.StringIO(
            "KTU 2.13\n"
            "id,surface form,morphological parsing,DULAT,POS,gloss,comments\n"
            "# KTU 2.13 2,,,,,,\n"
            "156656,adtumy,ad(t/t,ảdt,N,lady,\n"
            ",,ủmy/+y,ủm,n f,mother,\n"
        )

        loaded = legacy_align.load_rows(
            rows,
            legacy_align.LEGACY_IDX,
            source="test.csv",
            delimiter=",",
        )

        self.assertEqual(
            loaded[("-", "2")][0][2],
            {"ad(t/t", "ủmy/+y"},
        )

    def test_historical_packed_alternatives_are_split(self):
        self.assertEqual(
            legacy_align.split_variants("l(I); l(II); l(III)", packed_variants=True),
            {"l(I)", "l(II)", "l(III)"},
        )

    def test_exact_homonym_subset_is_not_collapsed_to_broad_agreement(self):
        automatic = {"l(I)", "l(II)", "l(III)"}

        result = legacy_align.verdict({"l(I)"}, automatic, proven_automatic_basis=True)

        self.assertEqual(result, "REJECTED-AUTO")
        self.assertEqual(
            legacy_align.rejected_options({"l(I)"}, automatic, result),
            {"l(II)", "l(III)"},
        )

    def test_seeded_extra_automatic_option_is_explicit_rejection(self):
        legacy = {"šlm/"}
        automatic = {"šlm/", "]š]lm[/"}

        result = legacy_align.verdict(legacy, automatic, proven_automatic_basis=True)

        self.assertEqual(result, "REJECTED-AUTO")
        self.assertEqual(legacy_align.rejected_options(legacy, automatic, result), {"]š]lm[/"})

    def test_equal_sets_remain_agreement(self):
        self.assertEqual(
            legacy_align.verdict({"šlm/"}, {"šlm/"}, proven_automatic_basis=True),
            "AGREE",
        )

    def test_extra_option_on_curated_row_does_not_infer_reviewer_rejection(self):
        self.assertEqual(
            legacy_align.verdict({"šlm/"}, {"šlm/", "]š]lm[/"}, proven_automatic_basis=False),
            "CURRENT-EXTRA",
        )

    def test_partial_overlap_is_generic_disagreement(self):
        self.assertEqual(
            legacy_align.verdict(
                {"šlm/", "legacy-only/"},
                {"šlm/", "automatic-only/"},
                proven_automatic_basis=True,
            ),
            "DIFFER",
        )

    def test_homonym_only_broadening_is_not_a_rejection(self):
        self.assertEqual(
            legacy_align.verdict({"ym/"}, {"ym(I)/"}, proven_automatic_basis=True),
            "AGREE~",
        )

    def test_explicit_homonym_conflict_is_not_broadened_into_rejection(self):
        self.assertEqual(
            legacy_align.verdict(
                {"mlk(I)/"},
                {"mlk(II)/", "mlk["},
                proven_automatic_basis=True,
            ),
            "DIFFER",
        )

    def test_seed_marker_without_historical_basis_does_not_prove_rejection(self):
        """Tania's blank-slate omission must remain ordinary silence."""
        self.assertEqual(
            legacy_align.verdict(
                {"šlm/"},
                {"šlm/", "]š]lm[/"},
                proven_automatic_basis=False,
            ),
            "CURRENT-EXTRA",
        )


if __name__ == "__main__":
    unittest.main()
