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
            self.assertEqual(result.pos, "n. m. sg.")

    def test_preserves_plain_nominal_variant_and_adds_enclitic_variant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'ỉl', 'I', 'n. m.')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'ỉlm', 'suff.', '', 'encl. -m')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'ỉlm', 'pl.', '', '')"
            )
            conn.commit()
            conn.close()

            fixer = DulatEncliticMFixer(db_path)
            row = TabletRow("2a", "ilm", "il(I)/m", "ỉl (I)", "n. m. pl.", "god", "")
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "il(I)/~m; il(I)/m")
            self.assertEqual(result.pos, "n. m. sg.; n. m. pl.")

    def test_rewrites_prefixed_finite_enclitic_without_dropping_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, '/m-t/', '', 'vb')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'ymtm', 'G, prefc.', '', 'encl. -m')"
            )
            conn.commit()
            conn.close()

            fixer = DulatEncliticMFixer(db_path)
            row = TabletRow("2b", "ymtm", "!y!mtm[", "/m-t/", "vb G prefc.", "to die", "")
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "!y!mt[~m")

    def test_preserves_hidden_radicals_when_appending_enclitic_m(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, '/ʔ-t-w/', '', 'vb')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'ảtm', 'G, impv.', '', 'encl. -m')"
            )
            conn.commit()
            conn.close()

            fixer = DulatEncliticMFixer(db_path)
            row = TabletRow("2c", "atm", "ʔtw[", "/ʔ-t-w/", "vb G impv.", "to come", "")
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "ʔtw[~m")

    def test_does_not_strip_root_final_m_from_existing_plain_variant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            _init_schema(conn)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) "
                "VALUES (1, 'šlm', 'II', 'n. m.')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'šlmm', 'suff.', '', 'encl. -m')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'šlmm', 'pl.', '', '')"
            )
            conn.commit()
            conn.close()

            fixer = DulatEncliticMFixer(db_path)
            row = TabletRow(
                "2d",
                "šlmm",
                "šlm(II)/~m; šlm(II)/m",
                "šlm (II); šlm (II)",
                "n. m. sg.; n. m. pl.",
                "communion victim / sacrifice; communion victim / sacrifice",
                "",
            )
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, row.analysis)

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
