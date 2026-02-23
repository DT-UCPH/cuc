import tempfile
import unittest
import sqlite3
from pathlib import Path
from typing import List, Tuple

from pipeline.instruction_refiner import InstructionRefiner


class InstructionRefinerTest(unittest.TestCase):
    def _create_dulat_db(self, path: Path, rows: List[Tuple[str, str, str]]) -> None:
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute("CREATE TABLE entries (lemma TEXT, homonym TEXT, gender TEXT)")
        cur.executemany(
            "INSERT INTO entries (lemma, homonym, gender) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
        conn.close()

    def test_marks_dulat_not_found_row_as_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.tsv"
            path.write_text(
                "#---------------------------- KTU 1.172 1\n"
                "1\tṣḥr\tṣḥr\t\t\t\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )

            refiner = InstructionRefiner()
            rows, changed = refiner.refine_file(path)
            self.assertEqual(rows, 1)
            self.assertEqual(changed, 1)

            out = path.read_text(encoding="utf-8").splitlines()[1]
            self.assertEqual(out, "1\tṣḥr\t?\t?\t?\t?\tDULAT: NOT FOUND")

    def test_normalizes_disallowed_col23_characters(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.tsv"
            path.write_text("1\tbʿl\tbʿl/\tbʕl (I)\tn.\tlord\n", encoding="utf-8")

            refiner = InstructionRefiner()
            rows, changed = refiner.refine_file(path)
            self.assertEqual(rows, 1)
            self.assertEqual(changed, 1)

            out = path.read_text(encoding="utf-8").strip()
            self.assertEqual(out, "1\tbˤl\tbˤl/\tbʕl (I)\tn.\tlord")

    def test_enriches_pos_gender_from_dulat(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            path = dir_path / "sample.tsv"
            db_path = dir_path / "dulat.sqlite3"
            self._create_dulat_db(
                db_path,
                [("mlk", "I", "m."), ("kbd", "IV", "f.")],
            )
            path.write_text(
                "1\tmlk\tmlk/\tmlk (I)\tn.\tking\n"
                "2\tkbd\tkbd/\tkbd (IV)\tadj.\theavy\n",
                encoding="utf-8",
            )

            refiner = InstructionRefiner(dulat_db=db_path)
            rows, changed = refiner.refine_file(path)
            self.assertEqual(rows, 2)
            self.assertEqual(changed, 2)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "1\tmlk\tmlk/\tmlk (I)\tn. m.\tking")
            self.assertEqual(lines[1], "2\tkbd\tkbd/\tkbd (IV)\tadj. f.\theavy")

    def test_keeps_pos_when_gender_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir)
            path = dir_path / "sample.tsv"
            db_path = dir_path / "dulat.sqlite3"
            self._create_dulat_db(
                db_path,
                [("x", "", "m."), ("x", "", "f.")],
            )
            path.write_text("1\tx\tx/\tx\tn.\titem\n", encoding="utf-8")

            refiner = InstructionRefiner(dulat_db=db_path)
            rows, changed = refiner.refine_file(path)
            self.assertEqual(rows, 1)
            self.assertEqual(changed, 0)

            out = path.read_text(encoding="utf-8").strip()
            self.assertEqual(out, "1\tx\tx/\tx\tn.\titem")


if __name__ == "__main__":
    unittest.main()
