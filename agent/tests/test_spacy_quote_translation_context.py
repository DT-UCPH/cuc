"""Focused tests for the generic quote-translation tie-breaker."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from spacy_ugaritic.doc_builder import build_doc, group_tablet_lines
from spacy_ugaritic.language import create_ugaritic_quote_translation_nlp


class SpacyQuoteTranslationContextTest(unittest.TestCase):
    def _build_translation_db(self, path: Path) -> None:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE entries (
              entry_id INTEGER PRIMARY KEY,
              lemma TEXT,
              homonym TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE attestations (
              entry_id INTEGER,
              stem_name TEXT,
              sense_definition TEXT,
              ug TEXT,
              translation TEXT,
              citation TEXT
            )
            """
        )
        cur.execute(
            "INSERT INTO entries(entry_id, lemma, homonym) VALUES (?, ?, ?)",
            (6001, "ym", "I"),
        )
        cur.execute(
            (
                "INSERT INTO attestations("
                "entry_id, stem_name, sense_definition, ug, translation, citation"
                ") VALUES (?, ?, ?, ?, ?, ?)"
            ),
            (
                6001,
                "",
                "",
                "b šbʕ ym",
                "on the seventh day",
                "CAT 1.14 III:2",
            ),
        )
        conn.commit()
        conn.close()

    def test_resolves_unique_candidate_from_quote_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_translation_db(db_path)
            nlp = create_ugaritic_quote_translation_nlp(dulat_db=db_path)
            grouped = group_tablet_lines(
                [
                    "# KTU 1.14 III:2\t\t\t\t\t\t",
                    "1\tym\tym(I)/\tym (I)\tn. m. sg. abs. gen.\tday\t",
                    "1\tym\tym(II)/\tym (II)\tn. m. sg. abs. gen.\tsea\t",
                    "2\tšbʕ\tšbˤ(I)/\tšbʕ (I)\tnum.\tseven\t",
                ]
            )
            doc = build_doc(nlp, grouped, source_name="KTU 1.14.tsv")
            resolved = nlp(doc)
            self.assertEqual([c.analysis for c in resolved[0]._.resolved_candidates], ["ym(I)/"])
            self.assertIn("DULAT quote", resolved[0]._.resolved_candidates[0].comment)
            self.assertIn("cue: day", resolved[0]._.resolved_candidates[0].comment)

    def test_skips_when_multiple_candidates_match_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_translation_db(db_path)
            nlp = create_ugaritic_quote_translation_nlp(dulat_db=db_path)
            grouped = group_tablet_lines(
                [
                    "# KTU 1.14 III:2\t\t\t\t\t\t",
                    "1\tym\tym(I)/\tym (I)\tn. m. sg. abs. gen.\tday\t",
                    "1\tym\tym(III)/\tym (III)\tn. m. sg. abs. gen.\tseventh day\t",
                ]
            )
            doc = build_doc(nlp, grouped, source_name="KTU 1.14.tsv")
            resolved = nlp(doc)
            self.assertEqual(
                [c.analysis for c in resolved[0]._.resolved_candidates],
                ["ym(I)/", "ym(III)/"],
            )


if __name__ == "__main__":
    unittest.main()
