import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.steps.attested_split_token_merge import AttestedSplitTokenMergeFixer


class AttestedSplitTokenMergeFixerTest(unittest.TestCase):
    def _init_dulat_db(self, path: Path) -> None:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE entries ("
            "entry_id INTEGER PRIMARY KEY, "
            "lemma TEXT, homonym TEXT, pos TEXT, "
            "wiki_transcription TEXT, summary TEXT, text TEXT)"
        )
        cur.execute(
            "CREATE TABLE senses (id INTEGER PRIMARY KEY, entry_id INTEGER, definition TEXT)"
        )
        cur.execute("CREATE TABLE translations (entry_id INTEGER, text TEXT)")
        cur.execute("CREATE TABLE forms (text TEXT, entry_id INTEGER, morphology TEXT)")
        cur.execute(
            "CREATE TABLE dulat_reverse_refs ("
            "norm_ref TEXT, entry_id INTEGER, payload TEXT, "
            "PRIMARY KEY(norm_ref, entry_id))"
        )
        cur.execute(
            "INSERT INTO entries("
            "entry_id, lemma, homonym, pos, wiki_transcription, summary, text"
            ") VALUES (2457, 'lản', '', 'n. m.', '', 'power', '')"
        )
        cur.execute("INSERT INTO translations(entry_id, text) VALUES (2457, 'power')")
        cur.execute("INSERT INTO senses(entry_id, definition) VALUES (2457, 'power')")
        cur.execute("INSERT INTO forms(text, entry_id, morphology) VALUES ('la', 2457, 'sg.')")
        cur.execute(
            "INSERT INTO forms(text, entry_id, morphology) VALUES ('lank', 2457, 'sg., suff.')"
        )
        cur.execute(
            "INSERT INTO dulat_reverse_refs(norm_ref, entry_id, payload) "
            "VALUES ('KTU 1.108:24', 2457, '{}')"
        )
        conn.commit()
        conn.close()

    def _init_udb_db(self, path: Path) -> None:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE ktu_to_dulat (ktu_ref TEXT, entry_id INTEGER)")
        conn.commit()
        conn.close()

    def test_adds_attested_merged_variant_for_adjacent_unresolved_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dulat_db = root / "dulat.sqlite"
            udb_db = root / "udb.sqlite"
            self._init_dulat_db(dulat_db)
            self._init_udb_db(udb_db)
            target = root / "KTU 1.108.tsv"
            target.write_text(
                "\n".join(
                    [
                        "# KTU 1.108 24\t\t\t\t\t\t",
                        "153335\tla\tla/\tlả\tn. m. sg.\tpower\t",
                        "# KTU 1.108 25\t\t\t\t\t\t",
                        "153336\tnk\t?\t?\t?\t?\tDULAT: NOT FOUND",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            fixer = AttestedSplitTokenMergeFixer(dulat_db=dulat_db, udb_db=udb_db)
            result = fixer.refine_file(target)

            self.assertEqual(result.rows_changed, 1)
            rows = target.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                (
                    "153335\tla\tlan/+k\tlản\tn. m. sg. cstr.\t"
                    "power\tIf merged with following token nk."
                ),
                rows,
            )

    def test_skips_when_second_token_is_already_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dulat_db = root / "dulat.sqlite"
            udb_db = root / "udb.sqlite"
            self._init_dulat_db(dulat_db)
            self._init_udb_db(udb_db)
            target = root / "KTU 1.108.tsv"
            target.write_text(
                "\n".join(
                    [
                        "# KTU 1.108 24\t\t\t\t\t\t",
                        "153335\tla\tla/\tlả\tn. m. sg.\tpower\t",
                        "# KTU 1.108 25\t\t\t\t\t\t",
                        "153336\tnk\tnk/\tnk\tn.\tthing\t",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            fixer = AttestedSplitTokenMergeFixer(dulat_db=dulat_db, udb_db=udb_db)
            result = fixer.refine_file(target)

            self.assertEqual(result.rows_changed, 0)
