"""Tests for forcing `l(III)`/`l(IV)` in context-specific references."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.l_functor_vocative_context import LFunctorVocativeContextDisambiguator


class LFunctorVocativeContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = LFunctorVocativeContextDisambiguator()

    def test_forces_l3_in_nominal_clause_reference(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.24:36\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "2\tảbnm\tảbn/m\tảbn\tn. m.\tstones\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertNotIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(II)\tl (II)\tadv.\tno\t", lines)

    def test_forces_l4_in_vocative_reference_before_noun(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.24:15\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tkṯrt\tkṯrt/\tkṯrt\tDN\tKotharat\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(IV)\tl (IV)\tinterj.\toh!\t", lines)
            self.assertNotIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)

    def test_skips_l4_reference_when_next_token_is_verbal(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.24:15\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\ttbʕ\t!t!bʕ[\t/t-b-ʕ/\tvb\tto go\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_does_not_force_when_only_different_column_is_attested(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.4 I:23\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tksỉ\tksỉ/\tksỉ\tn. m.\tthrone\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_resolves_overlapping_l3_l4_reference_by_next_token_pos(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.17 I:23\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\ttbrknn\t!t!brkn[n\t/b-r-k/\tvb\tto bless\t\n"
            "3\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "3\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "4\tṯr\tṯr(I)/\tṯr (I)\tn. m.\tbull\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 7)
            self.assertEqual(result.rows_changed, 4)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertIn("3\tl\tl(IV)\tl (IV)\tinterj.\toh!\t", lines)
            self.assertNotIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(II)\tl (II)\tadv.\tno\t", lines)
            self.assertNotIn("3\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("3\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)


if __name__ == "__main__":
    unittest.main()
