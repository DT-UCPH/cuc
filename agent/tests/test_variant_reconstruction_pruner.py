"""Pruning of non-reconstructable variant rows that have healthy siblings.

Regression source: cross-token leakage rows such as `gh -> ytn[` (KTU 1.16
II:36, 1.17, 1.5 IV:6) survive refinement next to the correct `g/+h` row and
can even win ranking. When at least one variant of a token reconstructs to
the surface, variants that cannot are parser artifacts and must be dropped.
"""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.variant_reconstruction_pruner import VariantReconstructionPruner

HEADER = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"


def _run(rows: list[str]) -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "KTU 1.test.tsv"
        body = "".join(r + "\n" for r in rows)
        path.write_text(HEADER + "# KTU 1.16 II:36\t\t\t\t\t\t\n" + body, encoding="utf-8")
        VariantReconstructionPruner().refine_file(path)
        return path.read_text(encoding="utf-8")


class VariantReconstructionPrunerTest(unittest.TestCase):
    def test_leakage_row_is_dropped_when_sibling_reconstructs(self) -> None:
        result = _run(
            [
                "1\tgh\tytn[\t/y-t-n/\tvb\tto give\t",
                "1\tgh\tg/+h\tg\tn. m. sg. cstr. nom.\t(loud) voice\t",
            ]
        )
        self.assertNotIn("ytn[", result)
        self.assertIn("g/+h", result)

    def test_all_non_reconstructable_variants_are_kept(self) -> None:
        result = _run(
            [
                "1\tṯṯb\t]š]ṯb[b\t/ṯ-(w)-b/\tvb Š impv. 2\tto send\t",
                "1\tṯṯb\t!!]š]ṯb[/b\t/ṯ-(w)-b/\tvb Š inf.\tto send\t",
            ]
        )
        self.assertIn("]š]ṯb[b", result)
        self.assertIn("!!]š]ṯb[/b", result)

    def test_single_row_token_is_never_dropped(self) -> None:
        result = _run(["1\tgh\tytn[\t/y-t-n/\tvb\tto give\t"])
        self.assertIn("ytn[", result)

    def test_unresolved_rows_are_preserved(self) -> None:
        result = _run(
            [
                "1\tgh\tg/+h\tg\tn. m. sg. cstr. nom.\t(loud) voice\t",
                "1\tgh\t?\t?\t?\t?\tneeds review",
            ]
        )
        self.assertIn("g/+h", result)
        self.assertIn("needs review", result)

    def test_broken_x_surfaces_are_untouched(self) -> None:
        result = _run(
            [
                "1\txxh\tg/+h\tg\tn. m.\tvoice\t",
                "1\txxh\tytn[\t/y-t-n/\tvb\tto give\t",
            ]
        )
        self.assertIn("ytn[", result)
        self.assertIn("g/+h", result)

    def test_merge_annotated_rows_are_untouched(self) -> None:
        result = _run(
            [
                "1\tsbn\tsb(b[ny\t/s-b-b/\tvb\tto go around\tMERGE WITH THE NEXT: sbn+y.",
                "2\ty\tsb(b[ny\t/s-b-b/\tvb\tto go around\tMERGE WITH THE PREVIOUS.",
            ]
        )
        self.assertEqual(result.count("sb(b[ny"), 2)


if __name__ == "__main__":
    unittest.main()
