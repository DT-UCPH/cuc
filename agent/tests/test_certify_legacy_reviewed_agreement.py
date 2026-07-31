from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.certify_legacy_reviewed_agreement import (
    SEED_MARK,
    certify_exact_agreements,
)


class CertifyLegacyReviewedAgreementTest(unittest.TestCase):
    def test_certifies_only_resolved_exact_seeded_analysis_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reviewed = root / "reviewed.tsv"
            legacy = root / "legacy.tsv"
            header = (
                "id\tsurface form\tsign span\tmorphological parsing\t"
                "DULAT\tPOS\tgloss\tcomments\n"
            )
            reviewed.write_text(
                header
                + f"1\tab\tab\tab/\tab\tn.\tword\t{SEED_MARK}\n"
                + f"1\tab\tab\tab(I)/\tab (I)\tn.\tword\t{SEED_MARK}\n"
                + f"2\tcd\tcd\tcd/\tcd\tn.\tword\t{SEED_MARK}\n"
                + f"3\tef\tef\t?\t?\t?\t?\t{SEED_MARK}\n"
                + "4\tgh\tgh\tgh/\tgh\tn.\tword\talready reviewed\n",
                encoding="utf-8",
            )
            legacy.write_text(
                header
                + "1\tab\tab\tab(I)/\t\t\t\t\n"
                + "1\tab\tab\tab/\t\t\t\t\n"
                + "2\tcd\tcd\tother/\t\t\t\tlegacy disagreement\n"
                + "3\tef\tef\t?\t?\t?\t?\tunresolved\n"
                + "4\tgh\tgh\tgh/\t\t\t\tlegacy note\n",
                encoding="utf-8",
            )

            output, certified, changed_rows = certify_exact_agreements(
                reviewed,
                legacy,
            )

        self.assertEqual(certified, 1)
        self.assertEqual(changed_rows, 2)
        self.assertIn("1\tab\tab\tab/\tab\tn.\tword\t", output)
        self.assertIn("1\tab\tab\tab(I)/\tab (I)\tn.\tword\t", output)
        self.assertIn(f"2\tcd\tcd\tcd/\tcd\tn.\tword\t{SEED_MARK}", output)
        self.assertIn(f"3\tef\tef\t?\t?\t?\t?\t{SEED_MARK}", output)
        self.assertIn("4\tgh\tgh\tgh/\tgh\tn.\tword\talready reviewed", output)
        self.assertNotIn("legacy note", output)

    def test_commented_exact_token_requires_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reviewed = root / "reviewed.tsv"
            legacy = root / "legacy.tsv"
            header = (
                "id\tsurface form\tsign span\tmorphological parsing\t"
                "DULAT\tPOS\tgloss\tcomments\n"
            )
            reviewed.write_text(
                header + f"1\tab\tab\tab/\tab\tn.\tword\t{SEED_MARK}\n",
                encoding="utf-8",
            )
            legacy.write_text(
                header + "1\tab\tab\tab/\t\t\t\texpert note\n",
                encoding="utf-8",
            )

            conservative, certified, _ = certify_exact_agreements(reviewed, legacy)
            included, included_count, _ = certify_exact_agreements(
                reviewed,
                legacy,
                include_commented=True,
            )

        self.assertEqual(certified, 0)
        self.assertIn(SEED_MARK, conservative)
        self.assertEqual(included_count, 1)
        self.assertIn("expert note", included)

    def test_honors_minimum_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reviewed = root / "reviewed.tsv"
            legacy = root / "legacy.tsv"
            text = (
                "id\tsurface form\tsign span\tmorphological parsing\t"
                "DULAT\tPOS\tgloss\tcomments\n"
                f"9\tab\tab\tab/\tab\tn.\tword\t{SEED_MARK}\n"
            )
            reviewed.write_text(text, encoding="utf-8")
            legacy.write_text(text.replace(SEED_MARK, "expert"), encoding="utf-8")

            output, certified, changed_rows = certify_exact_agreements(
                reviewed,
                legacy,
                minimum_id=10,
            )

        self.assertEqual((certified, changed_rows), (0, 0))
        self.assertIn(SEED_MARK, output)


if __name__ == "__main__":
    unittest.main()
