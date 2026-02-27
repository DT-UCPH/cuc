"""Regression tests for /b-ʕ-l/ verbal analysis slash normalization linting."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterBaalVerbalSlashTest(unittest.TestCase):
    def _lint_messages(self, body: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n" + body,
                encoding="utf-8",
            )
            issues = lint_file(
                path=path,
                dulat_forms={},
                entry_meta={},
                lemma_map={},
                entry_stems={},
                entry_gender={},
                udb_words=None,
                baseline=None,
                input_format="auto",
                db_checks=False,
            )
            return [issue.message for issue in issues]

    def test_flags_missing_slash_for_baal_verbal_variant(self) -> None:
        msgs = self._lint_messages("1\tbˤl\tbˤl[\t/b-ʕ-l/\tvb\tto make\t\n")
        self.assertIn(
            "For /b-ʕ-l/ verbal readings, use canonical analysis with `[/` (e.g., bˤl[/)",
            msgs,
        )

    def test_does_not_flag_when_baal_verbal_variant_is_canonical(self) -> None:
        msgs = self._lint_messages("1\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb\tto make\t\n")
        self.assertNotIn(
            "For /b-ʕ-l/ verbal readings, use canonical analysis with `[/` (e.g., bˤl[/)",
            msgs,
        )


if __name__ == "__main__":
    unittest.main()
