"""Tests for contextual disambiguation of `ydk` rows."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.ydk_context_disambiguator import YdkContextDisambiguator


class YdkContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = YdkContextDisambiguator()

    def test_collapses_ydk_when_followed_by_sgr(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "146856\tydk\tyd(I)/+k\tyd (I)\tn. f.\thand\t\n"
            "146856\tydk\tyd(I)/+k=\tyd (I)\tn. f.\thand\t\n"
            "146856\tydk\tyd(II)/+k\tyd (II)\tn. m.\tlove\t\n"
            "146856\tydk\tyd(II)/+k=\tyd (II)\tn. m.\tlove\t\n"
            "146856\tydk\t!y!dk[\td-k(-k)/\tvb\tto be pounded\t\n"
            "146856\tydk\t!y=!dk[\td-k(-k)/\tvb\tto be pounded\t\n"
            "146857\tṣġr\tṣġr(I)/\tṣġr (I)\tadj. m.\tsmall\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.22.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 7)
            self.assertEqual(result.rows_changed, 6)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1],
                "146856\tydk\tyd(II)/+k=\tyd (II)\tn. m.\tlove\t",
            )
            self.assertEqual(lines[2], "146857\tṣġr\tṣġr(I)/\tṣġr (I)\tadj. m.\tsmall\t")
            self.assertEqual(sum(1 for line in lines if "\tydk\t" in line), 1)

    def test_leaves_ydk_unchanged_without_sgr_context(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "146856\tydk\tyd(II)/+k=\tyd (II)\tn. m.\tlove\t\n"
            "146857\tġzr\tġzr/\tġzr\tn. m.\tlad\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.22.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 2)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
