"""Structural cell checks: empty analysis cells and comma-packed variants.

Regression source: KTU 1.5 V:5 (id 140215) shipped with an empty parsing
cell, and auto rows like `+km, +km=` or `+y, [y` pack several analysis
variants into one cell, breaking the one-variant-per-row format.
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


def _lint_rows(rows: list[str]) -> list:
    header = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.7"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "KTU 1.test.tsv"
        path.write_text(header + "".join(r + "\n" for r in rows), encoding="utf-8")
        return lint_file(
            path=path,
            dulat_forms={},
            entry_meta={},
            lemma_map={},
            entry_stems={},
            entry_gender={},
            udb_words=None,
            baseline=None,
            input_format="auto",
            db_checks=False,
        )


class LinterStructuralCellsTest(unittest.TestCase):
    def test_empty_analysis_cell_is_error(self) -> None:
        issues = _lint_rows(["1\tn\t\t-n (IV)\tcontracted suff. pn.\thim\t"])
        hits = [(x.level, x.message) for x in issues if "Empty morphological parsing" in x.message]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][0], "error")

    def test_placeholder_analysis_cell_is_not_empty_error(self) -> None:
        issues = _lint_rows(["1\txxxk\t?\t?\t?\t?\t"])
        hits = [x for x in issues if "Empty morphological parsing" in x.message]
        self.assertFalse(hits)

    def test_comma_packed_analysis_cell_is_error(self) -> None:
        issues = _lint_rows(["1\tkm\t+km, +km=\t-km\t\t\t"])
        hits = [(x.level, x.message) for x in issues if "Comma-packed" in x.message]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][0], "error")

    def test_single_variant_analysis_has_no_structural_issue(self) -> None:
        issues = _lint_rows(["1\tkm\tkm\tkm\tprep.\tlike\t"])
        hits = [
            x
            for x in issues
            if "Comma-packed" in x.message or "Empty morphological parsing" in x.message
        ]
        self.assertFalse(hits)


if __name__ == "__main__":
    unittest.main()
