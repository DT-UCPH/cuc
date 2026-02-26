"""Tests for pruning non-verbal `l(II)` negation rows."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.l_negation_verb_context import LNegationVerbContextPruner


class LNegationVerbContextPrunerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = LNegationVerbContextPruner()

    def test_prunes_l2_from_ambiguous_group_before_nonverb(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu/Baal\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertNotIn("1\tl\tl(II)\tl (II)\tadv.\tno\t", lines)
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)

    def test_keeps_l2_before_verb(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tytn\t!y!(ytn[\t/y-t-n/\tvb\tto give\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_keeps_single_l2_row_when_it_is_the_only_option(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu/Baal\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 2)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_forces_single_l2_in_ktu_1_3_iv_5_exception(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 IV:5\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu/Baal\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(II)\tl (II)\tadv.\tno\t", lines)
            self.assertNotIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)

    def test_forces_l2_when_exception_group_lost_l2_variant(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 IV:5\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu/Baal\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(II)\tl (II)\tadv.\tno\t", lines)
            self.assertNotIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)

    def test_forces_single_l2_in_ktu_4_213_exception_range(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 4.213:10\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tṭb\tṭb/\tṭb\tadj.\tgood\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 4.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(II)\tl (II)\tadv.\tno\t", lines)
            self.assertNotIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)


if __name__ == "__main__":
    unittest.main()
