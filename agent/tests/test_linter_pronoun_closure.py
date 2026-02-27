"""Regression tests for pronoun '/' closure linting."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterPronounClosureTest(unittest.TestCase):
    def test_warns_when_pronoun_uses_nominal_slash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\thw\thw/\thw\tpers. pn.\the, it\t\n"
                ),
                encoding="utf-8",
            )

            hw_entry = DulatEntry(
                entry_id=1,
                lemma="hw",
                homonym="",
                pos="pers. pn.",
                gloss="he, it",
                morph="sg., nom.",
                form_text="hw",
            )
            dulat_forms = {normalize_surface("hw"): [hw_entry]}
            entry_meta = {1: ("hw", "", "pers. pn.", "he, it")}
            lemma_map = {normalize_surface("hw"): [hw_entry]}
            entry_stems = {}
            entry_gender = {}
            udb_words = {normalize_udb("hw")}

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
            self.assertIn("Pronouns should not use '/' closure in analysis", messages)

    def test_no_warning_when_pronoun_has_no_slash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\thw\thw\thw\tpers. pn.\the, it\t\n"
                ),
                encoding="utf-8",
            )

            hw_entry = DulatEntry(
                entry_id=1,
                lemma="hw",
                homonym="",
                pos="pers. pn.",
                gloss="he, it",
                morph="sg., nom.",
                form_text="hw",
            )
            dulat_forms = {normalize_surface("hw"): [hw_entry]}
            entry_meta = {1: ("hw", "", "pers. pn.", "he, it")}
            lemma_map = {normalize_surface("hw"): [hw_entry]}
            entry_stems = {}
            entry_gender = {}
            udb_words = {normalize_udb("hw")}

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
            self.assertNotIn("Pronouns should not use '/' closure in analysis", messages)


if __name__ == "__main__":
    unittest.main()
