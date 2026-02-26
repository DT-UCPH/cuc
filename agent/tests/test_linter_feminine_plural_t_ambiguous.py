"""Regression tests for feminine /t= warning on sg/pl-ambiguous DULAT forms."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterFemininePluralAmbiguousTest(unittest.TestCase):
    def test_does_not_require_t_equal_when_surface_has_both_sg_and_pl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tthmt\tthm(t/t\tthmt\tn. f.\tPrimordial Ocean\t\n"
                ),
                encoding="utf-8",
            )

            thmt_sg = DulatEntry(
                entry_id=1,
                lemma="thmt",
                homonym="",
                pos="n.",
                gloss="Primordial Ocean",
                morph="sg.",
                form_text="thmt",
            )
            thmt_pl = DulatEntry(
                entry_id=1,
                lemma="thmt",
                homonym="",
                pos="n.",
                gloss="Primordial Ocean",
                morph="pl.",
                form_text="thmt",
            )

            dulat_forms = {normalize_surface("thmt"): [thmt_sg, thmt_pl]}
            entry_meta = {1: ("thmt", "", "n.", "Primordial Ocean")}
            lemma_map = {normalize_surface("thmt"): [thmt_sg]}
            entry_stems = {}
            entry_gender = {1: "f."}
            udb_words = {normalize_udb("thmt")}

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
                "Feminine plural noun in DULAT should use '/t='",
                messages,
            )


if __name__ == "__main__":
    unittest.main()
