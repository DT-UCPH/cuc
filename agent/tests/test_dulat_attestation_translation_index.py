"""Unit tests for DULAT attestation translation/sense lookup."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.dulat_attestation_translation_index import (
    DulatAttestationTranslationIndex,
)


class DulatAttestationTranslationIndexTest(unittest.TestCase):
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
              stem_name TEXT,
              sense_definition TEXT,
              ug TEXT,
              translation TEXT,
              citation TEXT
            )
            """
        )
        cur.executemany(
            "INSERT INTO entries(entry_id, lemma, homonym) VALUES (?, ?, ?)",
            [
                (4039, "/š-l-m/", ""),
                (5001, "l", "III"),
                (5002, "k", "I"),
            ],
        )
        cur.executemany(
            (
                "INSERT INTO attestations("
                "entry_id, stem_name, sense_definition, ug, translation, citation"
                ") "
                "VALUES (?, ?, ?, ?, ?, ?)"
            ),
            [
                (
                    4039,
                    "D",
                    "to restore / preserve health",
                    "tšlmk",
                    "may the gods protect you, keep you healthy",
                    "CAT 2.11:9",
                ),
                (
                    4039,
                    "G",
                    "to be well, do well, be in peace",
                    "šlm",
                    "may my mother be well",
                    "CAT 2.13:7",
                ),
                (
                    5001,
                    "",
                    "",
                    "l",
                    "certainly",
                    "CAT 2.10 5",
                ),
                (
                    5002,
                    "",
                    "",
                    "yd ỉlm p k mtm ʕz mỉd",
                    "here the power of gods is like death / DN (of) an utter strength",
                    "CAT 2.10:13",
                ),
            ],
        )
        conn.commit()
        conn.close()

    def test_from_sqlite_loads_reference_translations_and_sense_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_db(db_path)
            index = DulatAttestationTranslationIndex.from_sqlite(db_path)

            self.assertEqual(
                index.translations_for_variant_token("l (III)", "CAT 2.10:5"),
                ("certainly",),
            )
            self.assertEqual(
                index.translations_for_surface_at_reference("k", "KTU 2.10:13"),
                ("here the power of gods is like death / DN (of) an utter strength",),
            )
            self.assertEqual(
                index.translation_evidence_for_surface_at_reference("k", "KTU 2.10:13")[0].article,
                "k (I)",
            )
            self.assertEqual(
                index.sense_definitions_for_entry(
                    4039,
                    "CAT 2.11:9",
                    stem_name="Dpass.",
                ),
                ("to restore / preserve health",),
            )
            self.assertEqual(
                index.sense_definitions_for_entry(
                    4039,
                    "KTU 2.13:7",
                    stem_name="G",
                ),
                ("to be well, do well, be in peace",),
            )


if __name__ == "__main__":
    unittest.main()
