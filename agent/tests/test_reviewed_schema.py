"""Expert feedback must not silently become shifted fields or phantom tokens."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file
from reviewed_evaluation.loader import MorphologyTsvLoader


HEADER = "id\tsurface form\tsign span\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
VALID = "158776\tqrdm\tqrdm  \tqrd(I)/~m\tqrd (I)\tn. m. sg.\thero\t"


class ReviewedSchemaTest(unittest.TestCase):
    def lint(self, path):
        return lint_file(
            path=path, dulat_forms={}, entry_meta={}, lemma_map={},
            entry_stems={}, entry_gender={}, udb_words=None, baseline=None,
            input_format="auto", db_checks=False,
        )

    def test_rejects_missing_extra_and_broken_records_before_normalization(self):
        malformed = [
            VALID.rstrip("\t"),
            VALID + "proposed analysis\textra field",
            "158817\taliynqrdm\taliyn/ . ",
            "qrdm\tqrd/~m ?\t?\t?\t?\tcomment",
            "qrdm\tqrdm\tqrdm\t?\t?\t?\t?\tcomment",
            VALID + "# comment\thidden tab",
        ]
        for row in malformed:
            with self.subTest(row=row), tempfile.TemporaryDirectory() as tmp:
                # Header, not directory name, identifies this schema.
                path = Path(tmp) / "expert.tsv"
                path.write_text(HEADER + row + "\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, r"expert.tsv:2: Expected"):
                    MorphologyTsvLoader().load(path)
                issues = self.lint(path)
                structural = [i for i in issues if i.message.startswith("Expected")]
                self.assertEqual(len(structural), 1)
                self.assertEqual(structural[0].level, "error")

    def test_accepts_alternatives_empty_surface_and_internal_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expert.tsv"
            path.write_text(
                HEADER + "# KTU 1.5 II:11\t\t\t\t\t\t\t\n"
                + VALID + "Tania Notarius: singular. ## Notation question pending.\n"
                + VALID.replace("qrd(I)/~m", "qrd(I)/m") + "\n"
                + "158777\t\t\t?\t?\t?\t?\t\n", encoding="utf-8",
            )
            dataset = MorphologyTsvLoader().load(path)
            self.assertEqual(dataset.token_count, 2)
            self.assertEqual(len(dataset.tokens_by_id["158776"].analyses), 2)
            self.assertFalse([i for i in self.lint(path) if i.message.startswith("Expected")])

    def test_legacy_seven_column_loader_keeps_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.tsv"
            path.write_text(
                HEADER.replace("sign span\t", "")
                + "1\tx\t?\t?\t?\t?\n", encoding="utf-8",
            )
            self.assertEqual(MorphologyTsvLoader().load(path).token_count, 1)


if __name__ == "__main__":
    unittest.main()
