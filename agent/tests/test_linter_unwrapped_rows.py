"""Tests for one-variant-per-row checks in out/*.tsv."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file

PACKED_MSG = (
    "Semicolon-packed variants are not allowed in out/*.tsv; split each option into its own row"
)
DUPLICATE_MSG = "Duplicate unwrapped row payload (same id, surface, and col3-col6)"


class LinterUnwrappedRowsTest(unittest.TestCase):
    HEADER = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"

    def _lint(self, body: str) -> list:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(self.HEADER + body, encoding="utf-8")
            return lint_file(
                path=path,
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

    def test_flags_packed_semicolon_variants(self) -> None:
        issues = self._lint("1\tabc\ta1;a2\td1;d2\tp1;p2\tg1;g2\t\n")
        messages = [issue.message for issue in issues]
        self.assertIn(PACKED_MSG, messages)

    def test_flags_duplicate_unwrapped_rows(self) -> None:
        issues = self._lint("1\tabc\ta1\td1\tp1\tg1\tnote 1\n1\tabc\ta1\td1\tp1\tg1\tnote 2\n")
        messages = [issue.message for issue in issues]
        self.assertTrue(any(DUPLICATE_MSG in message for message in messages))

    def test_allows_distinct_variants_for_same_id_surface(self) -> None:
        issues = self._lint("1\tabc\ta1\td1\tp1\tg1\t\n1\tabc\ta2\td2\tp2\tg2\t\n")
        messages = [issue.message for issue in issues]
        self.assertFalse(any(DUPLICATE_MSG in message for message in messages))
        self.assertNotIn(PACKED_MSG, messages)


if __name__ == "__main__":
    unittest.main()
