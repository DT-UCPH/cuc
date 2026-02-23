"""Tests for strict out/*.tsv 7-column schema enforcement."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterSchemaEnforcementTest(unittest.TestCase):
    HEADER = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"

    def _lint_text(self, text: str) -> list:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            file_path = out_dir / "KTU 1.test.tsv"
            file_path.write_text(text, encoding="utf-8")
            return lint_file(
                path=file_path,
                dulat_forms={},
                entry_meta={},
                lemma_map={},
                entry_stems={},
                entry_gender={},
                udb_words=set(),
                baseline=None,
                input_format="auto",
                db_checks=False,
            )

    def test_out_row_requires_exactly_7_columns(self) -> None:
        issues = self._lint_text(self.HEADER + "# KTU 1.test 1\n1\ta\ta/\ta\tn.\tgloss\n")
        self.assertTrue(
            any("Expected exactly 7 columns" in issue.message for issue in issues),
            "Expected strict 7-column schema error for 6-column row.",
        )

    def test_hash_in_comment_column_does_not_break_schema(self) -> None:
        issues = self._lint_text(self.HEADER + "# KTU 1.test 1\n1\ta\ta/\ta\tn.\tgloss\t# note\n")
        self.assertFalse(any("Expected exactly 7 columns" in issue.message for issue in issues))
        self.assertFalse(any("Non-numeric line id" in issue.message for issue in issues))

    def test_out_file_requires_header_row(self) -> None:
        issues = self._lint_text("# KTU 1.test 1\n1\ta\ta/\ta\tn.\tgloss\t\n")
        self.assertTrue(
            any("Missing or invalid TSV header row" in issue.message for issue in issues)
        )


if __name__ == "__main__":
    unittest.main()
