"""Focused tests for the spaCy-based `k`-context component."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from spacy_ugaritic.doc_builder import build_doc, group_tablet_lines
from spacy_ugaritic.language import create_ugaritic_k_context_nlp


class SpacyKContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_k_context_nlp()

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

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.3.tsv"):
        grouped = group_tablet_lines(lines)
        doc = build_doc(self.nlp, grouped, source_name=source_name)
        return self.nlp(doc)

    def test_forces_k_iii_before_target_verb_bigram(self) -> None:
        doc = self._doc_from_lines(
            "1\tk\t+k\t-k (I)\t\t\t",
            "1\tk\t~k\t-k (II)\t\t\t",
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t",
            "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["k(III)"])

    def test_skips_for_non_target_surface(self) -> None:
        doc = self._doc_from_lines(
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t",
            "2\tilm\til(I)/m\tỉl (I)\tn. m.\tgod\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["k(III)", "k(I)"])

    def test_skips_when_target_surface_is_nonverbal(self) -> None:
        doc = self._doc_from_lines(
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t",
            "2\tyṣḥ\tyṣḥ/\tyṣḥ\tn. m.\tshout\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["k(III)", "k(I)"])

    def test_uses_citation_translation_as_last_resort(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_translation_db(db_path)
            nlp = create_ugaritic_k_context_nlp(dulat_db=db_path)
            grouped = group_tablet_lines(
                [
                    "# KTU 2.10 13\t\t\t\t\t\t",
                    "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
                    "1\tk\tk(I)\tk (I)\tprep.\tlike\t",
                    "2\tmtm\tmt/\tmt\tn. m.\tdeath\t",
                ]
            )
            doc = build_doc(nlp, grouped, source_name="KTU 2.10.tsv")
            resolved = nlp(doc)
            self.assertEqual([c.analysis for c in resolved[0]._.resolved_candidates], ["k(I)"])
            self.assertIn("DULAT quote", resolved[0]._.resolved_candidates[0].comment)
            self.assertIn("cue: like", resolved[0]._.resolved_candidates[0].comment)


if __name__ == "__main__":
    unittest.main()
