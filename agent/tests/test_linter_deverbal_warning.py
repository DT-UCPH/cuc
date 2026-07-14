"""Regression tests for deverbal noun/verb ambiguity severity."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterDeverbalWarningTest(unittest.TestCase):
    MESSAGE = "Deverbal form matches both verb and noun entries in DULAT"

    def test_deverbal_dual_match_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "auto_parsing" / "0.2.6"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbˤl\tbˤl[/\tbʕl (I)\tvb G act. ptcpl. m.\tto make\t\n"
                ),
                encoding="utf-8",
            )

            noun = DulatEntry(
                entry_id=1,
                lemma="bʕl",
                homonym="I",
                pos="n.",
                gloss="labourer",
                morph="n. m.",
                form_text="bˤl",
            )
            verb = DulatEntry(
                entry_id=2,
                lemma="/b-ʕ-l/",
                homonym="",
                pos="vb",
                gloss="to make",
                morph="G, act. ptc.",
                form_text="bˤl",
            )

            dulat_forms = {normalize_surface("bˤl"): [noun, verb]}
            entry_meta = {
                noun.entry_id: (noun.lemma, noun.homonym, noun.pos, noun.gloss),
                verb.entry_id: (verb.lemma, verb.homonym, verb.pos, verb.gloss),
            }
            lemma_map = {
                normalize_surface(noun.lemma): [noun],
                normalize_surface(verb.lemma): [verb],
            }
            entry_stems = {verb.entry_id: {"G"}}
            entry_gender = {}
            udb_words = {normalize_udb("bˤl")}

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

            matches = [issue for issue in issues if issue.message == self.MESSAGE]
            self.assertTrue(matches)
            self.assertTrue(all(issue.level == "warning" for issue in matches))


if __name__ == "__main__":
    unittest.main()
