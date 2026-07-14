"""Tests for form-morph overrides applied during DULAT loading in linter."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from linter.lint import load_dulat, normalize_surface


class LinterDulatFormMorphOverridesTest(unittest.TestCase):
    def test_overrides_il_construct_morphology_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE entries(
                    entry_id INTEGER PRIMARY KEY,
                    lemma TEXT,
                    homonym TEXT,
                    pos TEXT,
                    data TEXT
                )
                """
            )
            cur.execute("CREATE TABLE translations(entry_id INTEGER, text TEXT)")
            cur.execute("CREATE TABLE forms(text TEXT, morphology TEXT, entry_id INTEGER)")
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, data) "
                "VALUES (264, 'ỉl', 'I', 'n.', '{}')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (264, 'god')")
            cur.executemany(
                "INSERT INTO forms(text, morphology, entry_id) VALUES (?, ?, 264)",
                [
                    ("ỉl", "sg."),
                    ("ỉl", "du., cstr."),
                    ("ỉly", "du., cstr."),
                ],
            )
            conn.commit()
            conn.close()

            forms_map, _entry_meta, _lemma_map, _entry_stems, _entry_gender = load_dulat(db_path)
            il_rows = forms_map[normalize_surface("ỉl")]
            ily_rows = forms_map[normalize_surface("ỉly")]

            self.assertIn("sg., cstr.", {row.morph for row in il_rows})
            self.assertNotIn("du., cstr.", {row.morph for row in il_rows})
            self.assertEqual({row.morph for row in ily_rows}, {"pl., cstr."})

    def test_load_dulat_applies_form_text_alias_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE entries(
                    entry_id INTEGER PRIMARY KEY,
                    lemma TEXT,
                    homonym TEXT,
                    pos TEXT,
                    data TEXT
                )
                """
            )
            cur.execute("CREATE TABLE translations(entry_id INTEGER, text TEXT)")
            cur.execute("CREATE TABLE forms(text TEXT, morphology TEXT, entry_id INTEGER)")
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, data) "
                "VALUES (2520, '/l-s-m/', '', 'vb', '{}')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (2520, 'to run')")
            cur.execute(
                "INSERT INTO forms(text, morphology, entry_id) VALUES (?, ?, ?)",
                ("tslmn", "G, prefc.", 2520),
            )
            conn.commit()
            conn.close()

            forms_map, _entry_meta, _lemma_map, _entry_stems, _entry_gender = load_dulat(db_path)
            tlsmn_rows = forms_map[normalize_surface("tlsmn")]
            self.assertEqual([row.entry_id for row in tlsmn_rows], [2520])

    def test_load_dulat_generates_weak_final_prefixed_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE entries(
                    entry_id INTEGER PRIMARY KEY,
                    lemma TEXT,
                    homonym TEXT,
                    pos TEXT,
                    data TEXT
                )
                """
            )
            cur.execute("CREATE TABLE translations(entry_id INTEGER, text TEXT)")
            cur.execute("CREATE TABLE forms(text TEXT, morphology TEXT, entry_id INTEGER)")
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, data) "
                "VALUES (5001, '/ġ-l-y/', '', 'vb', '{}')"
            )
            cur.execute(
                "INSERT INTO translations(entry_id, text) VALUES (5001, 'to lose vitality')"
            )
            cur.execute(
                "INSERT INTO forms(text, morphology, entry_id) VALUES (?, ?, ?)",
                ("tġly", "D, prefc.", 5001),
            )
            conn.commit()
            conn.close()

            forms_map, _entry_meta, _lemma_map, _entry_stems, _entry_gender = load_dulat(db_path)
            tgl_rows = forms_map[normalize_surface("tġl")]
            self.assertEqual([row.entry_id for row in tgl_rows], [5001])

    def test_load_dulat_uses_forms_block_fallback_from_entry_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE entries(
                    entry_id INTEGER PRIMARY KEY,
                    lemma TEXT,
                    homonym TEXT,
                    pos TEXT,
                    data TEXT,
                    text TEXT
                )
                """
            )
            cur.execute("CREATE TABLE translations(entry_id INTEGER, text TEXT)")
            cur.execute("CREATE TABLE forms(text TEXT, morphology TEXT, entry_id INTEGER)")
            entry_text = (
                "<b>¶ Forms:</b> G suffc. <i>ġly</i>; prefc. <i>yġly</i>; inf. <i>ġly</i>. "
                "D suffc. <i>ġltm</i>; prefc. <i>tġly</i>, <i>tġl</i> (?). <br><b>G</b>."
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, data, text) "
                "VALUES (5002, '/ġ-l-y/', '', 'vb', '{}', ?)",
                (entry_text,),
            )
            cur.executemany(
                "INSERT INTO forms(text, morphology, entry_id) VALUES (?, ?, 5002)",
                [
                    ("ġly", "G, suffc."),
                    ("yġly", "G, prefc."),
                    ("ġly", "G, inf."),
                ],
            )
            cur.execute(
                "INSERT INTO translations(entry_id, text) VALUES (5002, 'to lose vitality')"
            )
            conn.commit()
            conn.close()

            forms_map, _entry_meta, _lemma_map, _entry_stems, _entry_gender = load_dulat(db_path)
            tgl_rows = forms_map[normalize_surface("tġl")]
            self.assertEqual([row.entry_id for row in tgl_rows], [5002])

    def test_load_dulat_ignores_word_break_suffix_standalone_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE entries(
                    entry_id INTEGER PRIMARY KEY,
                    lemma TEXT,
                    homonym TEXT,
                    pos TEXT,
                    data TEXT,
                    text TEXT
                )
                """
            )
            cur.execute("CREATE TABLE translations(entry_id INTEGER, text TEXT)")
            cur.execute("CREATE TABLE forms(text TEXT, morphology TEXT, entry_id INTEGER)")
            entry_text = (
                "<b>¶ Forms:</b> prefc. <i>ytn</i>{.}<i>hm</i>, <i>ytnn</i>, "
                "<i>ytn</i>{.}<i>nn</i>; impv. <i>tn</i>. <br><b>G</b>."
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, data, text) "
                "VALUES (5003, '/y-t-n/', '', 'vb', '{}', ?)",
                (entry_text,),
            )
            cur.execute(
                "INSERT INTO forms(text, morphology, entry_id) VALUES (?, ?, ?)",
                ("ytn", "G, prefc.", 5003),
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (5003, 'to give')")
            conn.commit()
            conn.close()

            forms_map, _entry_meta, _lemma_map, _entry_stems, _entry_gender = load_dulat(db_path)
            self.assertIn(normalize_surface("ytnhm"), forms_map)
            self.assertIn(normalize_surface("ytnnn"), forms_map)
            self.assertNotIn(normalize_surface("hm"), forms_map)
            self.assertNotIn(normalize_surface("nn"), forms_map)

    def test_overrides_thm_tahmak_suffix_morphology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE entries(
                    entry_id INTEGER PRIMARY KEY,
                    lemma TEXT,
                    homonym TEXT,
                    pos TEXT,
                    data TEXT
                )
                """
            )
            cur.execute("CREATE TABLE translations(entry_id INTEGER, text TEXT)")
            cur.execute("CREATE TABLE forms(text TEXT, morphology TEXT, entry_id INTEGER)")
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, data) "
                "VALUES (4268, 'tḥm', '', 'n.', '{}')"
            )
            cur.execute("INSERT INTO translations(entry_id, text) VALUES (4268, 'message')")
            cur.execute(
                "INSERT INTO forms(text, morphology, entry_id) VALUES (?, ?, ?)",
                ("tḥmk", "sg.", 4268),
            )
            conn.commit()
            conn.close()

            forms_map, _entry_meta, _lemma_map, _entry_stems, _entry_gender = load_dulat(db_path)
            tḥmk_rows = forms_map[normalize_surface("tḥmk")]
            self.assertEqual({row.morph for row in tḥmk_rows}, {"suff."})


if __name__ == "__main__":
    unittest.main()
