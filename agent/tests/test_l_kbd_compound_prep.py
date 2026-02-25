"""Tests for `l + kbd(I)` compound-preposition normalization."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.l_kbd_compound_prep import LKbdCompoundPrepDisambiguator


class LKbdCompoundPrepDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = LKbdCompoundPrepDisambiguator()

    def test_collapses_l_kbd_to_compound_prep_parsing(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 III:16\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tkbd\tkbd(II)/\tkbd (II)\tn. m.\ttotal (quantity or price)\t\n"
            "2\tkbd\tkbd(I)/\tkbd (I)\tn.\tliver\t\n"
            "2\tkbd\tkbd[\t/k-b-d/\tvb\tto honour\t\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 7)
            self.assertEqual(result.rows_changed, 5)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(II)\tl (II)\tadv.\tno\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertIn("2\tkbd\tkbd(I)/\tkbd (I)\tn.\twithin\t", lines)
            self.assertNotIn(
                "2\tkbd\tkbd(II)/\tkbd (II)\tn. m.\ttotal (quantity or price)\t",
                lines,
            )
            self.assertNotIn("2\tkbd\tkbd[\t/k-b-d/\tvb\tto honour\t", lines)

    def test_skips_when_kbd_i_variant_is_absent(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tkbd\tkbd(II)/\tkbd (II)\tn. m.\ttotal (quantity or price)\t\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_restores_l_i_when_only_l_iii_remains(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 IV:24\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tkbd\tkbd(I)/\tkbd (I)\tn.\tliver\t\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertIn("2\tkbd\tkbd(I)/\tkbd (I)\tn.\twithin\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertNotIn("2\tkbd\tkbd(I)/\tkbd (I)\tn.\tliver\t", lines)


if __name__ == "__main__":
    unittest.main()
