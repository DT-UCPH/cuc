"""Tests for slash-variant handling in refine_results_mentions helpers."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.refine_results_mentions import (
    Entry,
    analysis_for_entry,
    build_variants,
    entry_label,
    load_entries,
)


class RefineResultsMentionsTest(unittest.TestCase):
    def _init_dulat_schema(self, db_path: Path) -> None:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE entries ("
            "entry_id INTEGER PRIMARY KEY, "
            "lemma TEXT, homonym TEXT, pos TEXT, wiki_transcription TEXT)"
        )
        cur.execute(
            "CREATE TABLE senses (id INTEGER PRIMARY KEY, entry_id INTEGER, definition TEXT)"
        )
        cur.execute("CREATE TABLE translations (entry_id INTEGER, text TEXT)")
        cur.execute("CREATE TABLE forms (text TEXT, entry_id INTEGER, morphology TEXT)")
        conn.commit()
        conn.close()

    def test_entry_label_preserves_short_prefix_slash_lemma(self) -> None:
        entry = Entry(
            entry_id=665,
            lemma="ỉ/ủšḫry",
            hom="",
            pos="DN",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(entry_label(entry), "ỉ/ủšḫry")

    def test_analysis_prefers_surface_for_short_prefix_slash_lemma(self) -> None:
        entry = Entry(
            entry_id=665,
            lemma="ỉ/ủšḫry",
            hom="",
            pos="DN",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("ušḫry", entry), "ušḫry/")
        self.assertEqual(analysis_for_entry("išḫry", entry), "išḫry/")

    def test_load_entries_falls_back_to_lemma_when_forms_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, wiki_transcription) "
                "VALUES (?, ?, ?, ?, ?)",
                (170, "ủgrt", "", "TN", ""),
            )
            cur.execute(
                "INSERT INTO senses(id, entry_id, definition) VALUES (?, ?, ?)",
                (1, 170, "Ugarit"),
            )
            conn.commit()
            conn.close()

            _entries_by_id, forms_map, _lemma_map, suffix_map, forms_morph = load_entries(db_path)
            self.assertIn("ugrt", forms_map)
            self.assertEqual([entry.entry_id for entry in forms_map["ugrt"]], [170])

            variants = build_variants(
                surface="ugrt",
                current_ref="CAT 1.119 I:1",
                forms_map=forms_map,
                suffix_map=suffix_map,
                forms_morph=forms_morph,
                mention_ids=set(),
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                max_variants=3,
            )
            self.assertTrue(variants)
            self.assertEqual(variants[0].entries[0].entry_id, 170)


if __name__ == "__main__":
    unittest.main()
