"""Tests for onomastic override TSV format handling."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.base import TabletRow
from pipeline.steps.onomastic_gloss import OnomasticGlossOverrideFixer


class OnomasticGlossOverrideFormatTest(unittest.TestCase):
    def test_three_column_tsv_uses_gloss_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            overrides_path = Path(tmp_dir) / "onomastic_gloss_overrides.tsv"
            overrides_path.write_text(
                "dulat\tPOS\tgloss\nỉl (I)\tDN m.\tʾIlu/El\n",
                encoding="utf-8",
            )

            fixer = OnomasticGlossOverrideFixer(overrides_path=overrides_path)
            row = TabletRow(
                line_id="1",
                surface="il",
                analysis="il(I)/",
                dulat="ỉl (I)",
                pos="DN",
                gloss="Ilu",
                comment="",
            )

            result = fixer.refine_row(row)
            self.assertEqual(result.gloss, "ʾIlu/El")

    def test_appends_missing_onomastic_variant_from_tsv_pos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            overrides_path = Path(tmp_dir) / "onomastic_gloss_overrides.tsv"
            overrides_path.write_text(
                "dulat\tPOS\tgloss\nšpš\tDN f.\tŠapšu/Shapsh/Shapshu\n",
                encoding="utf-8",
            )

            fixer = OnomasticGlossOverrideFixer(overrides_path=overrides_path)
            row = TabletRow(
                line_id="2",
                surface="špš",
                analysis="špš/",
                dulat="špš",
                pos="n. f. sg.",
                gloss="sun",
                comment="",
            )

            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "špš/; špš/")
            self.assertEqual(result.dulat, "špš; špš")
            self.assertEqual(result.pos, "DN f.; n. f. sg.")
            self.assertEqual(result.gloss, "Šapšu/Shapsh/Shapshu; sun")

    def test_does_not_append_onomastic_variant_for_inflected_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            overrides_path = Path(tmp_dir) / "onomastic_gloss_overrides.tsv"
            overrides_path.write_text(
                "dulat\tPOS\tgloss\nỉl (I)\tDN m.\tʾIlu/Ilu/El\n",
                encoding="utf-8",
            )

            fixer = OnomasticGlossOverrideFixer(overrides_path=overrides_path)
            row = TabletRow(
                line_id="3",
                surface="ilm",
                analysis="il(I)/m",
                dulat="ỉl (I)",
                pos="n. m. pl.",
                gloss="god",
                comment="",
            )

            result = fixer.refine_row(row)
            self.assertEqual(result, row)


if __name__ == "__main__":
    unittest.main()
