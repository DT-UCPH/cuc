"""Unit tests for DULAT attestation index generation and lookup."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.dulat_attestation_index import (
    DulatAttestationIndex,
    parse_dulat_head_token,
)


class DulatAttestationIndexTest(unittest.TestCase):
    def _build_db(self, path: Path) -> None:
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
              ug TEXT,
              translation TEXT,
              citation TEXT,
              kind TEXT
            )
            """
        )
        cur.executemany(
            "INSERT INTO entries(entry_id, lemma, homonym) VALUES (?, ?, ?)",
            [
                (1, "bʕl", "I"),
                (2, "bʕl", "II"),
                (3, "/q-t-l/", ""),
            ],
        )
        cur.executemany(
            (
                "INSERT INTO attestations(entry_id, ug, translation, citation, kind) "
                "VALUES (?, '', '', '', 'attestation')"
            ),
            [
                (1,),
                (1,),
                (2,),
                (2,),
                (2,),
                (3,),
            ],
        )
        conn.commit()
        conn.close()

    def test_parse_dulat_head_token_uses_first_entry(self) -> None:
        self.assertEqual(parse_dulat_head_token("bʕl (II), -m (I)"), ("bʕl", "II"))
        self.assertEqual(parse_dulat_head_token("/q-t-l/"), ("/q-t-l/", ""))
        self.assertEqual(parse_dulat_head_token("?"), ("", ""))

    def test_from_sqlite_and_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_db(db_path)
            index = DulatAttestationIndex.from_sqlite(db_path)

            self.assertEqual(index.count_for_variant_token("bʕl (II)"), 3)
            self.assertEqual(index.count_for_variant_token("bʕl"), 3)
            self.assertEqual(index.count_for_variant_token("/q-t-l/"), 1)
            self.assertEqual(index.count_for_variant_token("missing"), -1)

    def test_missing_db_returns_empty_index(self) -> None:
        index = DulatAttestationIndex.from_sqlite(Path("does-not-exist.sqlite"))
        self.assertEqual(index.count_for_variant_token("bʕl (II)"), -1)


if __name__ == "__main__":
    unittest.main()
