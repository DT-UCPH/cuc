"""File-level tests for the integrated spaCy-based formula context step."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_formula_context import SpacyFormulaContextDisambiguator


class SpacyFormulaContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyFormulaContextDisambiguator()

    def test_resolves_bigram_formula(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\taliyn\taliyn/\tảlỉyn\tadj. m.\tThe Very / Most Powerful\tkeep\n"
            "2\tbˤl\tbˤl(II)/;bˤl[\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\tkeep\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[2],
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu\tkeep",
            )

    def test_resolves_trigram_formula(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tidk\tidk\tỉdk\tnarrative adv. functor\tthen\t\n"
            "2\tl\tl(I);l(II);l(III)\tl (I);l (II);l (III)\tprep.;adv.;functor\tto;no;certainly\t\n"
            "3\tttn\tytn[\t/y-t-n/\tvb\tto give\t\n"
            "4\tpnm\tpn(m/m\tpnm\tn. m. pl. tant.\tface\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "2\tl\tl(III)\tl (III)\tfunctor\tcertainly\t")

    def test_resolves_grouped_token_variants_as_single_formula_reading(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tzbl\tzbl(I)/\tzbl (I)\tn. m.\tprince\tkeep\n"
            "2\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\tbʕl (II);bʕl (I);/b-ʕ-l/"
            "\tn. m./DN;n. m.;vb\tBaʿlu;labourer;to make\tkeep\n"
            "2\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\tbʕl (II);bʕl (I);/b-ʕ-l/"
            "\tn. m./DN;n. m.;vb\tBaʿlu;labourer;to make\tkeep\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertGreaterEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines,
                [
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments",
                    "1\tzbl\tzbl(I)/\tzbl (I)\tn. m.\tprince\tkeep",
                    "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu\tkeep",
                ],
            )

    def test_resolves_rkb_arpt_epithet_to_nominal_rkb(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\trkb\trkb[/;rkb(I)/\t/r-k-b/;rkb (I)\tvb;n. m.\tto mount;Charioteer\tkeep\n"
            "2\tˤrpt\tˤrp(t/t\tʕrpt\tn. f.\tcloud(s)\tkeep\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertGreaterEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1],
                "1\trkb\trkb(I)/\trkb (I)\tn. m.\tCharioteer\tkeep",
            )


if __name__ == "__main__":
    unittest.main()
