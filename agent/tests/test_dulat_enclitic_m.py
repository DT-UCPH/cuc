"""Regression tests for DULAT note-backed enclitic `-m` rewriting."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.steps.base import TabletRow
from pipeline.steps.dulat_enclitic_m import DulatEncliticMFixer


def _init_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE entries(entry_id INTEGER PRIMARY KEY, lemma TEXT, homonym TEXT, pos TEXT)"
    )
    cur.execute(
        "CREATE TABLE forms(entry_id INTEGER, text TEXT, morphology TEXT, cert TEXT, notes TEXT)"
    )
    conn.commit()


class DulatEncliticMFixerTest(unittest.TestCase):
    def test_rewrites_weak_final_infinitive_to_hidden_radical_plus_enclitic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, '/b-k-y/', '', 'vb')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'bkm', 'G, inf.', '', 'encl. -m')"
            )
            conn.commit()
            conn.close()

            fixer = DulatEncliticMFixer(db_path)
            row = TabletRow("1", "bkm", "!!bkm[/", "/b-k-y/", "vb G inf.", "to weep", "")
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "!!bk(y[/~m")

    def test_rewrites_nominal_surface_with_enclitic_m(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'ủgr', 'I', 'n. m.')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'ủgrm', 'sg., suff.', '', 'encl. -m')"
            )
            conn.commit()
            conn.close()

            fixer = DulatEncliticMFixer(db_path)
            row = TabletRow("2", "ủgrm", "ủgrm(I)/", "ủgr (I)", "n. m.", "field", "")
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "ủgr(I)/~m")

    def test_leaves_row_unchanged_without_note_backing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, '/b-k-y/', '', 'vb')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'bkm', 'G, inf.', '', '')"
            )
            conn.commit()
            conn.close()

            fixer = DulatEncliticMFixer(db_path)
            row = TabletRow("3", "bkm", "!!bkm[/", "/b-k-y/", "vb G inf.", "to weep", "")
            self.assertEqual(fixer.refine_row(row), row)


if __name__ == "__main__":
    unittest.main()
