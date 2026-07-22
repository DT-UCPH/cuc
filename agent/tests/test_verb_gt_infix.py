"""Tests for the scoped Gt-infix regeneration step."""

import unittest
from pathlib import Path

from pipeline.steps.base import TabletRow
from pipeline.steps.verb_gt_infix import VerbGtInfixFixer


class VerbGtInfixFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = VerbGtInfixFixer(Path("unused.sqlite"))

    def test_repairs_firm_gt_row(self) -> None:
        row = TabletRow(
            "154981",
            "yitmr",
            "!y!(ʔ&itmr[",
            "/ʔ-m-r/",
            "vb Gt prefc. 3 m. sg.",
            "to be seen",
            "",
        )
        rewritten = self.fixer.refine_row(row)
        self.assertEqual(rewritten.analysis, "!y!(ʔ&i]t]mr[")

    def test_leaves_other_rows_unchanged(self) -> None:
        row = TabletRow("1", "yqtl", "!y!qtl[", "/q-t-l/", "vb G prefc.", "kill", "")
        self.assertEqual(self.fixer.refine_row(row), row)


if __name__ == "__main__":
    unittest.main()
