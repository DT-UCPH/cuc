"""File-level tests for the integrated spaCy-based `k`-context step."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_k_context import SpacyKContextDisambiguator


class SpacyKContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyKContextDisambiguator()

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
            (5002, "k", "I"),
        )
        cur.execute(
            (
                "INSERT INTO attestations("
                "entry_id, stem_name, sense_definition, ug, translation, citation"
                ") VALUES (?, ?, ?, ?, ?, ?)"
            ),
            (
                5002,
                "",
                "",
                "yd ỉlm p k mtm ʕz mỉd",
                "here the power of gods is like death / DN (of) an utter strength",
                "CAT 2.10:13",
            ),
        )
        conn.commit()
        conn.close()

    def test_forces_k_iii_before_target_verb_bigram(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\t+k\t-k (I)\t\t\tplus\n"
            "1\tk\t~k\t-k (II)\t\t\tclitic\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\tprep\n"
            "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\tplus",
                lines,
            )

    def test_uses_citation_translation_as_last_resort(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 2.10 13\t\t\t\t\t\t\n"
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
            "2\tmtm\tmt/\tmt\tn. m.\tdeath\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 2.10.tsv"
            db_path = Path(tmp_dir) / "dulat.sqlite"
            path.write_text(content, encoding="utf-8")
            self._build_translation_db(db_path)

            step = SpacyKContextDisambiguator(dulat_db=db_path)
            result = step.refine_file(path)

            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertTrue(
                any(
                    line.startswith("1\tk\tk(I)\tk (I)\tprep.\tlike\t")
                    and "DULAT quote in k (I)" in line
                    and "cue: like" in line
                    for line in lines
                )
            )
            self.assertNotIn(
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
                lines,
            )


if __name__ == "__main__":
    unittest.main()
