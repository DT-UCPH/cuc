"""Regression tests for gender validation on feminine surface forms."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterFormGenderMatchTest(unittest.TestCase):
    def test_allows_feminine_pos_when_surface_form_is_feminine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tpḥlt\tpḥl/t\tpḥl\tn. f.\tass\t\n"
                ),
                encoding="utf-8",
            )

            pahl = DulatEntry(
                entry_id=1,
                lemma="pḥl",
                homonym="",
                pos="n.",
                gloss="ass",
                morph="f.",
                form_text="pḥlt",
            )
            dulat_forms = {normalize_surface("pḥlt"): [pahl]}
            entry_meta = {1: ("pḥl", "", "n.", "ass")}
            lemma_map = {normalize_surface("pḥl"): [pahl]}
            entry_stems = {}
            entry_gender = {1: "m."}
            udb_words = {normalize_udb("pḥlt")}

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
                "Noun POS gender mismatch for pḥl: expected n. m., got n. f.",
                messages,
            )

    def test_does_not_treat_suff_as_feminine_for_gender_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tabn\tab/+n\tảb\tn. f.\tfather\t\n"
                ),
                encoding="utf-8",
            )

            ab = DulatEntry(
                entry_id=1,
                lemma="ảb",
                homonym="",
                pos="n.",
                gloss="father",
                morph="sg., suff.",
                form_text="abn",
            )
            dulat_forms = {normalize_surface("abn"): [ab]}
            entry_meta = {1: ("ảb", "", "n.", "father")}
            lemma_map = {normalize_surface("ảb"): [ab]}
            entry_stems = {}
            entry_gender = {1: "m."}
            udb_words = {normalize_udb("abn")}

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
                "Noun POS gender mismatch for ảb: expected n. m., got n. f.",
                messages,
            )


if __name__ == "__main__":
    unittest.main()
