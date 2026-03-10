"""File-level tests for the integrated spaCy-based `l`-context step."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_l_context import SpacyLContextDisambiguator


class SpacyLContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyLContextDisambiguator()

    def test_forces_l_ii_for_reference_exception(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 IV:5\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\tkeep me\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\tprefer me\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tdrop me\n"
            "2\tib\tib(I)/\tỉb (I)\tn. m. sg.\tenemy\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "1\tl\tl(II)\tl (II)\tadv.\tno\tprefer me")

    def test_resolves_l_kbd_compound(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 III:16\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tfrom l\n"
            "2\tkbd\tkbd(I)/\tkbd (I)\tn.\tliver\tfrom noun\n"
            "2\tkbd\tkbd[\t/k-b-d/\tvb\tto honour\tfrom verb\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\tfrom l", lines)
            self.assertIn("2\tkbd\tkbd(I)/\tkbd (I)\tn.\twithin\tfrom noun", lines)

    def test_builds_l_kbd_compound_when_only_noncanonical_kbd_survives(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 III:16\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tfrom l\n"
            "2\tkbd\tkbd(II)/\tkbd (II)\tn. m.\ttotal\tfrom noun\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\tfrom l", lines)
            self.assertIn("2\tkbd\tkbd(I)/\tkbd (I)\tn.\twithin\tfrom noun", lines)

    def test_prefers_l_i_before_non_verbal_token(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.5 II:2\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\tkeep me\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\tdrop me\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tdrop me too\n"
            "2\tšmm\tšm(m(I)/m\tšmm (I)\tn. m. pl.\theavens\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "1\tl\tl(I)\tl (I)\tprep.\tto\tkeep me")

    def test_uses_attestation_translation_to_force_l_ii(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            db_path = root / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE entries (entry_id INTEGER PRIMARY KEY, lemma TEXT, homonym TEXT)"
            )
            cur.execute(
                "CREATE TABLE attestations (entry_id INTEGER, translation TEXT, citation TEXT)"
            )
            cur.execute("INSERT INTO entries(entry_id, lemma, homonym) VALUES (1, 'l', 'II')")
            cur.execute(
                "INSERT INTO attestations(entry_id, translation, citation) VALUES (?, ?, ?)",
                (1, "a lawful wife he did not get (keep)", "CAT 1.14 I:12"),
            )
            conn.commit()
            conn.close()

            step = SpacyLContextDisambiguator(dulat_db=db_path)
            path = root / "KTU 1.test.tsv"
            path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.14 I:12\n"
                "1\tl\tl(I)\tl (I)\tprep.\tto\tkeep me\n"
                "1\tl\tl(II)\tl (II)\tadv.\tno\tkeep me too\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tdrop me\n"
                "2\typq\t!y!pq[\t/p-q-y/\tvb G prefc.\tto get\t\n",
                encoding="utf-8",
            )

            result = step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "1\tl\tl(II)\tl (II)\tadv.\tno\tkeep me too")
