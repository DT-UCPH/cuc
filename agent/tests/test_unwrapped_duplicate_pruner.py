"""Tests for duplicate pruning after variant-row unwrapping."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.unwrapped_duplicate_pruner import UnwrappedDuplicatePruner


class UnwrappedDuplicatePrunerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = UnwrappedDuplicatePruner()

    def test_prunes_duplicate_payload_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tk\tk(I)\tk (I)\tprep.\tlike\tfirst\n"
                    "1\tk\tk(I)\tk (I)\tprep.\tlike\tsecond\n"
                    "1\tk\tk(II)\tk (II)\temph. functor\tyes\t\n"
                ),
                encoding="utf-8",
            )

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[1], "1\tk\tk(I)\tk (I)\tprep.\tlike\tfirst")
            self.assertEqual(lines[2], "1\tk\tk(II)\tk (II)\temph. functor\tyes\t")

    def test_keeps_distinct_payload_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
                    "1\tk\tk(II)\tk (II)\temph. functor\tyes\t\n"
                ),
                encoding="utf-8",
            )

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 0)


if __name__ == "__main__":
    unittest.main()
