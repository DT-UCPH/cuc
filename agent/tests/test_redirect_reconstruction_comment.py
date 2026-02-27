"""Tests for redirect-derived reconstruction provenance comments."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.redirect_reconstruction_comment import (
    RedirectReconstructionCommentFixer,
)


class RedirectReconstructionCommentFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = RedirectReconstructionCommentFixer()

    def test_marks_non_arrow_rows_in_redirect_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tšbˤr\t]š]bˤr(I)[\t/b-ʕ-r/ (I)\tvb\tto illuminate\t\n"
                    "1\tšbˤr\tšbˤr\tšbʕr\t→\t?\t\n"
                ),
                encoding="utf-8",
            )

            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                "\tBased on DULAT reconstruction.",
                lines[1],
            )
            self.assertTrue(lines[2].endswith("\t"))

    def test_keeps_existing_comment_and_avoids_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\trdmn\t(prdmn/\tprdmn\tDN\tSchar\texisting note\n"
                    "2\trdmn\trdmn\trdmn\t→\t?\t\n"
                ),
                encoding="utf-8",
            )

            self.fixer.refine_file(path)
            self.fixer.refine_file(path)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                "existing note Based on DULAT reconstruction.",
                lines[1],
            )
            self.assertEqual(lines[1].count("Based on DULAT reconstruction."), 1)


if __name__ == "__main__":
    unittest.main()
