"""Unit tests for bootstrap DULAT lookup behavior."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.bootstrap_tablet_labeling import load_dulat_forms, process_file


def _init_bootstrap_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("CREATE TABLE translations(entry_id INTEGER, text TEXT)")
    cur.execute(
        "CREATE TABLE entries(entry_id INTEGER PRIMARY KEY, lemma TEXT, homonym TEXT, pos TEXT)"
    )
    cur.execute(
        "CREATE TABLE forms(entry_id INTEGER, text TEXT, morphology TEXT, cert TEXT, notes TEXT)"
    )
    cur.execute(
        "CREATE TABLE attestations("
        "entry_id INTEGER, ug TEXT, translation TEXT, citation TEXT, kind TEXT)"
    )
    conn.commit()


class BootstrapTabletLabelingTest(unittest.TestCase):
    def test_fallback_prefers_ktu1_family_for_homonym_lemmas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_bootstrap_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'tnn', 'I', 'DN')"
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (2, 'tnn', 'II', 'PN')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (1, 'dragon')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (1, 'CAT 1.6 VI:51')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (2, 'CAT 4.35:13')")
            conn.commit()
            conn.close()

            forms_map = load_dulat_forms(db_path)
            self.assertIn("tnn", forms_map)
            ids = {e.entry_id for e in forms_map["tnn"]}
            self.assertEqual(ids, {1})

    def test_fallback_prefers_ktu1_homonyms_for_other_lemmas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_bootstrap_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'abc', 'I', 'n. m.')"
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (2, 'abc', 'II', 'PN')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (1, 'first')")
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (2, 'second')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (1, 'CAT 1.1 I:1')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (2, 'CAT 4.35:13')")
            conn.commit()
            conn.close()

            forms_map = load_dulat_forms(db_path)
            self.assertIn("abc", forms_map)
            ids = {e.entry_id for e in forms_map["abc"]}
            self.assertEqual(ids, {1})

    def test_fallback_keeps_all_when_no_ktu1_family_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_bootstrap_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'xyz', 'I', 'n. m.')"
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (2, 'xyz', 'II', 'PN')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (1, 'first')")
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (2, 'second')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (1, 'CAT 4.1:1')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (2, 'CAT 4.35:13')")
            conn.commit()
            conn.close()

            forms_map = load_dulat_forms(db_path)
            self.assertIn("xyz", forms_map)
            ids = {e.entry_id for e in forms_map["xyz"]}
            self.assertEqual(ids, {1, 2})

    def test_load_dulat_forms_falls_back_to_lemma_when_form_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_bootstrap_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'tnn', 'I', 'DN')"
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (2, 'tnn', 'II', 'PN')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (1, 'dragon')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (1, 'CAT 1.6 VI:51')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (2, 'CAT 1.16 V:31')")
            conn.commit()
            conn.close()

            forms_map = load_dulat_forms(db_path)
            self.assertIn("tnn", forms_map)
            ids = {e.entry_id for e in forms_map["tnn"]}
            self.assertEqual(ids, {1, 2})

    def test_load_dulat_forms_keeps_form_lookup_priority_over_lemma_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_bootstrap_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'abc', 'I', 'DN')"
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (2, 'abc', 'II', 'PN')"
            )
            cur.execute("INSERT INTO forms(entry_id, text) VALUES (1, 'abc')")
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (1, 'first')")
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (2, 'second')")
            conn.commit()
            conn.close()

            forms_map = load_dulat_forms(db_path)
            self.assertIn("abc", forms_map)
            ids = {e.entry_id for e in forms_map["abc"]}
            self.assertEqual(ids, {1})

    def test_process_file_resolves_token_from_lemma_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            in_path = Path(tmp_dir) / "in.tsv"
            out_path = Path(tmp_dir) / "out.tsv"
            conn = sqlite3.connect(db_path)
            _init_bootstrap_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'tnn', 'I', 'DN')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (1, 'dragon')")
            cur.execute("INSERT INTO attestations(entry_id, citation) VALUES (1, 'CAT 1.6 VI:51')")
            conn.commit()
            conn.close()

            in_path.write_text("1\ttnn\n", encoding="utf-8")
            forms_map = load_dulat_forms(db_path)
            process_file(in_path, out_path, forms_map)
            line = out_path.read_text(encoding="utf-8").splitlines()[0]

            self.assertNotIn("DULAT: NOT FOUND", line)
            self.assertIn("\ttnn(I)/\ttnn (I)\tDN\tdragon\t", line)


if __name__ == "__main__":
    unittest.main()
