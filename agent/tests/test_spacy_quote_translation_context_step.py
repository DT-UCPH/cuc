"""File-level tests for the generic quote-translation tie-breaker step."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_quote_translation_context import SpacyQuoteTranslationDisambiguator


class SpacyQuoteTranslationDisambiguatorTest(unittest.TestCase):
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

    def test_resolves_generic_homonym_and_writes_comment(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.14 III:2\t\t\t\t\t\t\n"
            "1\tym\tym(I)/\tym (I)\tn. m. sg. abs. gen.\tday\t\n"
            "1\tym\tym(II)/\tym (II)\tn. m. sg. abs. gen.\tsea\t\n"
            "2\tšbʕ\tšbˤ(I)/\tšbʕ (I)\tnum.\tseven\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.14.tsv"
            db_path = Path(tmp_dir) / "dulat.sqlite"
            path.write_text(content, encoding="utf-8")
            self._build_translation_db(db_path)

            step = SpacyQuoteTranslationDisambiguator(dulat_db=db_path)
            result = step.refine_file(path)

            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            resolved_line = next(
                line for line in lines if line.startswith("1\tym\tym(I)/\tym (I)\t")
            )
            self.assertIn(
                "DULAT quote KTU 1.14 III:2 (cue: day)",
                resolved_line,
            )
            self.assertNotIn("1\tym\tym(II)/\tym (II)\tn. m. sg. abs. gen.\tsea\t", lines)


if __name__ == "__main__":
    unittest.main()
