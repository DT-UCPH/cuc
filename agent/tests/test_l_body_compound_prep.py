"""Tests for `l + body-part` compound-preposition normalization."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.l_body_compound_prep import LBodyCompoundPrepDisambiguator


class LBodyCompoundPrepDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = LBodyCompoundPrepDisambiguator()

    def test_collapses_l_paan_to_compound_prep(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tpˤn\tpˤn/\tpʕn\tn. f.\tfoot\t\n"
            "3\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertIn("2\tpˤn\tpˤn/\tpʕn\tn. f.\tat the feet of\t", lines)
            self.assertNotIn("2\tpˤn\tpˤn/\tpʕn\tn. f.\tfoot\t", lines)

    def test_collapses_l_zaar_to_compound_prep(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tẓr\tẓr(I)/\tẓr (I)\tn. m.\tback\t\n"
            "3\tqdqdh\tqdqd/h\tqdqd\tn. m.\tskull\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("2\tẓr\tẓr(I)/\tẓr (I)\tn. m.\tupon\t", lines)
            self.assertNotIn("2\tẓr\tẓr(I)/\tẓr (I)\tn. m.\tback\t", lines)

    def test_skips_when_second_target_variant_is_missing(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tpˤn\tpˤn(II)\tpʕn (II)\tn. m.\tother\t\n"
            "3\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
