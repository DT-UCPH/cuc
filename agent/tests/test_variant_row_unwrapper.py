"""Tests for one-variant-per-row unwrapping of packed semicolon payloads."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.variant_row_unwrapper import VariantRowUnwrapper


class VariantRowUnwrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = VariantRowUnwrapper()

    def test_unwraps_aligned_variants_into_multiple_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tabc\ta1;a2\td1;d2\tp1;p2\tg1;g2\tnote\n"
                ),
                encoding="utf-8",
            )

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 1)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[1], "1\tabc\ta1\td1\tp1\tg1\tnote")
            self.assertEqual(lines[2], "1\tabc\ta2\td2\tp2\tg2\tnote")

    def test_reuses_singleton_payload_for_sparse_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tabc\ta1;a2\td1\tp1;p2\tg1\t\n"
                ),
                encoding="utf-8",
            )

            self.step.refine_file(path)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[1], "1\tabc\ta1\td1\tp1\tg1\t")
            self.assertEqual(lines[2], "1\tabc\ta2\td1\tp2\tg1\t")

    def test_deduplicates_identical_variants_after_unwrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tabc\ta1;a1\td1;d1\tp1;p1\tg1;g1\tnote\n"
                ),
                encoding="utf-8",
            )

            self.step.refine_file(path)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[1], "1\tabc\ta1\td1\tp1\tg1\tnote")

    def test_preserves_empty_slot_alignment_for_k_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tk\t+k; ~k; k(III); k(I); k(II)\t"
                    "-k (I); -k (II); k (III); k (I); k (II)\t"
                    ";;Subordinating or completive functor; prep.; emph. functor\t"
                    "when; like; yes\t\n"
                ),
                encoding="utf-8",
            )

            self.step.refine_file(path)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[1], "1\tk\t+k\t-k (I)\t\t\t")
            self.assertEqual(lines[2], "1\tk\t~k\t-k (II)\t\t\t")
            self.assertEqual(
                lines[3],
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
            )
            self.assertEqual(lines[4], "1\tk\tk(I)\tk (I)\tprep.\tlike\t")
            self.assertEqual(lines[5], "1\tk\tk(II)\tk (II)\temph. functor\tyes\t")


if __name__ == "__main__":
    unittest.main()
