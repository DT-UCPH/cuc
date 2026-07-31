"""Entry-metadata patches for defective DULAT cache rows.

Regression source: cache entry 2727 carries lemma 'mlk (I)' with empty
homonym and empty POS, so 'mlk' lookups miss the most common reading
('king') entirely - reported by Elijah for KTU 2.23 and visible across the
letter corpus.
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from dulat_patches import load_dulat_entry_patches
from linter.lint import load_dulat
from scripts.refine_results_mentions import load_entries


class LoadDulatEntryPatchesTest(unittest.TestCase):
    def test_loads_rows_keyed_by_entry_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "dulat_entry_patches.tsv"
            path.write_text(
                "entry_id\tlemma\thomonym\tpos\n2727\tmlk\tI\tn. m.\n",
                encoding="utf-8",
            )
            patches = load_dulat_entry_patches(path)
        self.assertEqual(patches, {2727: {"lemma": "mlk", "homonym": "I", "pos": "n. m."}})

    def test_missing_file_yields_no_patches(self) -> None:
        self.assertEqual(load_dulat_entry_patches(Path("/nonexistent/patches.tsv")), {})

    def test_blank_fields_are_not_patched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "dulat_entry_patches.tsv"
            path.write_text("entry_id\tlemma\thomonym\tpos\n10\t\t\tDN\n", encoding="utf-8")
            patches = load_dulat_entry_patches(path)
        self.assertEqual(patches, {10: {"pos": "DN"}})


class LoadEntriesAppliesPatchesTest(unittest.TestCase):
    def _make_db(self, path: Path) -> None:
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE entries (entry_id INTEGER, lemma TEXT, homonym TEXT, pos TEXT,"
            " wiki_transcription TEXT, summary TEXT, text TEXT)"
        )
        cur.execute(
            "INSERT INTO entries VALUES (2727, 'mlk (I)', '', '', '', 'king, sovereign', '')"
        )
        cur.execute(
            "CREATE TABLE senses (entry_id INTEGER, id INTEGER, stem_id INTEGER, definition TEXT)"
        )
        cur.execute("CREATE TABLE translations (entry_id INTEGER, text TEXT)")
        cur.execute("INSERT INTO translations VALUES (2727, 'king, sovereign')")
        cur.execute("CREATE TABLE forms (entry_id INTEGER, text TEXT, morphology TEXT)")
        cur.execute("INSERT INTO forms VALUES (2727, 'mlk', 'sg.')")
        cur.execute(
            "CREATE TABLE stems (id INTEGER, entry_id INTEGER, name TEXT, gloss TEXT, notes TEXT)"
        )
        conn.commit()
        conn.close()

    def test_patched_entry_gets_pos_and_homonym(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._make_db(db_path)
            entries_by_id, _forms, lemma_map, _suffix, _morph = load_entries(
                db_path,
                entry_patches={2727: {"lemma": "mlk", "homonym": "I", "pos": "n. m."}},
            )
        entry = entries_by_id[2727]
        self.assertEqual(entry.lemma, "mlk")
        self.assertEqual(entry.hom, "I")
        self.assertEqual(entry.pos, "n. m.")
        self.assertIn(2727, [e.entry_id for e in lemma_map.get("mlk", [])])

    def test_linter_loader_applies_repository_entry_patches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                "CREATE TABLE entries (entry_id INTEGER, lemma TEXT, homonym TEXT, "
                "pos TEXT, data TEXT, text TEXT)"
            )
            conn.execute(
                "INSERT INTO entries VALUES (5436, 't', '', 'vb', '{}', '')"
            )
            conn.execute("CREATE TABLE translations (entry_id INTEGER, text TEXT)")
            conn.execute(
                "CREATE TABLE forms (entry_id INTEGER, text TEXT, morphology TEXT)"
            )
            conn.commit()
            conn.close()

            _forms, entry_meta, lemma_map, _stems, _gender = load_dulat(db_path)

        self.assertEqual(entry_meta[5436][:3], ("-t", "", "morph."))
        self.assertIn(5436, [entry.entry_id for entry in lemma_map["-t"]])


if __name__ == "__main__":
    unittest.main()
