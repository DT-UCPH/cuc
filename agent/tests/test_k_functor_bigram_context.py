"""Tests for forcing `k(III)` in high-frequency verb-leading bigrams."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.k_functor_bigram_context import KFunctorBigramContextDisambiguator


class KFunctorBigramContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = KFunctorBigramContextDisambiguator()

    def test_forces_k_iii_before_target_verb_bigram(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\t+k\t-k (I)\t\t\t\n"
            "1\tk\t~k\t-k (II)\t\t\t\n"
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
            "1\tk\tk(II)\tk (II)\temph. functor\tyes\t\n"
            "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 6)
            self.assertEqual(result.rows_changed, 4)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
                lines,
            )
            self.assertNotIn("1\tk\tk(I)\tk (I)\tprep.\tlike\t", lines)
            self.assertNotIn("1\tk\tk(II)\tk (II)\temph. functor\tyes\t", lines)

    def test_skips_for_non_target_next_surface(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
            "2\tilm\til(I)/m\tỉl (I)\tn. m.\tgod\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_skips_when_next_target_surface_is_nonverbal(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
            "2\tyṣḥ\tyṣḥ/\tyṣḥ\tn. m.\tshout\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
