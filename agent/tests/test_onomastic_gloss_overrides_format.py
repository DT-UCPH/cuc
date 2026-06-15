"""Tests for onomastic override TSV format handling."""

import tempfile
import unittest
from pathlib import Path

from pipeline.dulat_attestation_index import DulatAttestationIndex, normalize_reference_label
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

    def test_refine_file_blocks_unattested_pn_append_when_non_pn_option_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            overrides_path = root / "onomastic_gloss_overrides.tsv"
            target = root / "KTU 1.5.tsv"
            overrides_path.write_text(
                "dulat\tPOS\tgloss\nšlyṭ\tPN m.\tŠaliyaṭu\n",
                encoding="utf-8",
            )
            target.write_text(
                "# KTU 1.5 I:3\t\t\t\t\t\t\n1\tšlyṭ\tšlyṭ/\tšlyṭ\tn. m. sg.\ttyrant\t\n",
                encoding="utf-8",
            )

            fixer = OnomasticGlossOverrideFixer(
                overrides_path=overrides_path,
                attestation_index=DulatAttestationIndex.empty(),
            )
            result = fixer.refine_file(target)

            self.assertEqual(result.rows_changed, 0)
            rows = target.read_text(encoding="utf-8").splitlines()
            self.assertEqual(rows[1], "1\tšlyṭ\tšlyṭ/\tšlyṭ\tn. m. sg.\ttyrant\t")

    def test_refine_file_keeps_directly_attested_pn_append(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            overrides_path = root / "onomastic_gloss_overrides.tsv"
            target = root / "KTU 1.5.tsv"
            overrides_path.write_text(
                "dulat\tPOS\tgloss\nšlyṭ\tPN m.\tŠaliyaṭu\n",
                encoding="utf-8",
            )
            target.write_text(
                "# KTU 1.5 I:3\t\t\t\t\t\t\n1\tšlyṭ\tšlyṭ/\tšlyṭ\tn. m. sg.\ttyrant\t\n",
                encoding="utf-8",
            )
            attestation_index = DulatAttestationIndex(
                counts_by_key={},
                max_count_by_lemma={},
                refs_by_key={("šlyṭ", ""): {normalize_reference_label("CAT 1.5 I:3")}},
            )

            fixer = OnomasticGlossOverrideFixer(
                overrides_path=overrides_path,
                attestation_index=attestation_index,
            )
            result = fixer.refine_file(target)

            self.assertEqual(result.rows_changed, 1)
            rows = target.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                rows[1],
                "1\tšlyṭ\tšlyṭ/; šlyṭ/\tšlyṭ; šlyṭ\tPN m.; n. m. sg.\tŠaliyaṭu; tyrant\t",
            )


if __name__ == "__main__":
    unittest.main()
