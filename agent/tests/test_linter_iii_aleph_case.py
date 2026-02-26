"""Regression tests for III-aleph case-vowel encoding warnings."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterIIIAlephCaseTest(unittest.TestCase):
    WARNING = (
        "III-aleph noun/adjective should encode lexeme-final case vowel as '(u|i|a' "
        "and inflection as '/&u|&i|&a'"
    )

    def test_warns_when_iii_aleph_case_encoding_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\trpi\trpu/\trpủ\tn. m.\thealer\t\n"
                ),
                encoding="utf-8",
            )

            rp_entry = DulatEntry(
                entry_id=1,
                lemma="rpủ",
                homonym="",
                pos="n.",
                gloss="healer",
                morph="sg.",
                form_text="rpỉ",
            )

            dulat_forms = {normalize_surface("rpỉ"): [rp_entry]}
            entry_meta = {1: ("rpủ", "", "n.", "healer")}
            lemma_map = {normalize_surface("rpủ"): [rp_entry]}
            entry_stems = {}
            entry_gender = {}
            udb_words = {normalize_udb("rpi")}

            issues = lint_file(
                path=path,
                dulat_forms=dulat_forms,
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems=entry_stems,
                entry_gender=entry_gender,
                udb_words=udb_words,
                baseline=None,
                input_format="auto",
                db_checks=True,
            )

            messages = [issue.message for issue in issues]
            self.assertIn(
                self.WARNING,
                messages,
            )

    def test_does_not_warn_when_iii_aleph_case_encoding_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\trpi\trp(u/&i\trpủ\tn. m.\thealer\t\n"
                ),
                encoding="utf-8",
            )

            rp_entry = DulatEntry(
                entry_id=1,
                lemma="rpủ",
                homonym="",
                pos="n.",
                gloss="healer",
                morph="sg.",
                form_text="rpỉ",
            )

            dulat_forms = {normalize_surface("rpỉ"): [rp_entry]}
            entry_meta = {1: ("rpủ", "", "n.", "healer")}
            lemma_map = {normalize_surface("rpủ"): [rp_entry]}
            entry_stems = {}
            entry_gender = {}
            udb_words = {normalize_udb("rpi")}

            issues = lint_file(
                path=path,
                dulat_forms=dulat_forms,
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems=entry_stems,
                entry_gender=entry_gender,
                udb_words=udb_words,
                baseline=None,
                input_format="auto",
                db_checks=True,
            )

            messages = [issue.message for issue in issues]
            self.assertNotIn(
                self.WARNING,
                messages,
            )


if __name__ == "__main__":
    unittest.main()
