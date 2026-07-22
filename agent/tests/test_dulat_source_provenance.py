"""Tests for source provenance on enriched DULAT cache records."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.dulat_source_provenance import (
    DulatSourceProvenanceIndex,
    append_provenance_comments,
)
from pipeline.steps.base import TabletRow
from pipeline.steps.dulat_source_provenance import DulatSourceProvenanceAnnotator
from scripts.annotate_dulat_source_provenance import annotate_file


def _database(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE entries ("
        "entry_id INTEGER PRIMARY KEY, lemma TEXT, homonym TEXT, data TEXT)"
    )
    conn.execute("CREATE TABLE translations (entry_id INTEGER, text TEXT)")
    rows = [
        (1, "mlk", "I", {}),
        (
            2,
            "w",
            "",
            {"source_created": "lupt", "article_source": "EUPT/LUPT"},
        ),
        (3, "ảdmn", "", {"article_source": "Huehnergard"}),
        (4, "w", "", {}),
        (5, "umt", "", {}),
        (6, "ủmt", "", {"article_source": "Huehnergard"}),
    ]
    conn.executemany(
        "INSERT INTO entries(entry_id, lemma, homonym, data) VALUES (?, ?, ?, ?)",
        [(entry_id, lemma, homonym, json.dumps(data)) for entry_id, lemma, homonym, data in rows],
    )
    conn.executemany(
        "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
        [
            (1, "king"),
            (2, "und"),
            (3, "red soil"),
            (4, "and"),
            (5, "family, clan"),
            (6, "clan, tribe"),
        ],
    )
    conn.commit()
    conn.close()


class DulatSourceProvenanceTest(unittest.TestCase):
    def test_resolves_only_source_derived_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dulat.sqlite"
            _database(db_path)
            index = DulatSourceProvenanceIndex.from_sqlite(db_path)
            self.assertEqual(index.sources_for_field("w"), ())
            self.assertEqual(index.sources_for_field("w", "und"), ("EUPT/LUPT",))
            self.assertEqual(index.sources_for_field("w", "and"), ())
            self.assertEqual(index.sources_for_field("umt", "clan, tribe"), ())
            self.assertEqual(
                index.sources_for_field("ủmt", "clan, tribe"), ("Huehnergard",)
            )
            self.assertEqual(index.sources_for_field("ảdmn"), ("Huehnergard",))
            self.assertEqual(index.sources_for_field("mlk (I)"), ())

    def test_annotator_preserves_existing_comment_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dulat.sqlite"
            _database(db_path)
            step = DulatSourceProvenanceAnnotator(db_path)
            row = TabletRow("1", "w", "w", "w", "conj.", "und", "Reviewed.")
            updated = step.refine_row(row)
            self.assertEqual(
                updated.comment,
                "Reviewed. | LUPT lemma",
            )
            self.assertEqual(step.refine_row(updated), updated)

    def test_annotator_includes_unresolved_rows_with_retained_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dulat.sqlite"
            out_path = Path(tmp) / "KTU 1.1.tsv"
            _database(db_path)
            out_path.write_text(
                "1\tw\t?\tw\t?\tund\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )
            step = DulatSourceProvenanceAnnotator(db_path)
            self.assertEqual(step.refine_file(out_path).rows_changed, 1)
            self.assertIn(
                "DULAT: NOT FOUND | LUPT lemma",
                out_path.read_text(encoding="utf-8"),
            )

    def test_reviewed_eight_column_file_keeps_sign_span(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dulat.sqlite"
            reviewed_path = Path(tmp) / "KTU 1.1.tsv"
            _database(db_path)
            reviewed_path.write_text(
                "1\tw\t[[w]]\tw\tw\tconj.\tund\tOld note.\n",
                encoding="utf-8",
            )
            index = DulatSourceProvenanceIndex.from_sqlite(db_path)
            self.assertEqual(annotate_file(reviewed_path, index), 1)
            self.assertEqual(annotate_file(reviewed_path, index), 0)
            self.assertEqual(
                reviewed_path.read_text(encoding="utf-8"),
                "1\tw\t[[w]]\tw\tw\tconj.\tund\tOld note. | LUPT lemma\n",
            )

    def test_reviewed_seven_column_file_is_annotated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dulat.sqlite"
            reviewed_path = Path(tmp) / "KTU 1.1.tsv"
            _database(db_path)
            reviewed_path.write_text(
                "1\tw\tw\tw\tconj.\tund\t\n",
                encoding="utf-8",
            )
            index = DulatSourceProvenanceIndex.from_sqlite(db_path)
            self.assertEqual(annotate_file(reviewed_path, index), 1)
            self.assertEqual(
                reviewed_path.read_text(encoding="utf-8"),
                "1\tw\tw\tw\tconj.\tund\tLUPT lemma\n",
            )

    def test_append_supports_multiple_sources(self) -> None:
        self.assertEqual(
            append_provenance_comments("", ("EUPT/LUPT", "Huehnergard")),
            "LUPT lemma | Huehnergard lemma",
        )

    def test_legacy_long_comment_is_shortened(self) -> None:
        self.assertEqual(
            append_provenance_comments(
                "Reviewed. | DULAT DB source: EUPT/LUPT (not original DULAT).",
                ("EUPT/LUPT",),
            ),
            "Reviewed. | LUPT lemma",
        )


if __name__ == "__main__":
    unittest.main()
