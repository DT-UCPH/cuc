"""File-level tests for the integrated spaCy-based lexical context steps."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_lexical_context import (
    SpacyBaalContextDisambiguator,
    SpacyYdkContextDisambiguator,
)


class SpacyBaalContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyBaalContextDisambiguator()

    def test_prunes_baal_labourer_outside_ktu4(self) -> None:
        content = "\n".join(
            [
                (
                    "1\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\tbʕl (II);bʕl (I);/b-ʕ-l/"
                    "\tn. m./DN;n. m.;vb\tBaʿlu;labourer;to make\t"
                ),
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[0],
                "1\tbˤl\tbˤl(II)/;bˤl[/\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\t",
            )

    def test_collapses_aliyn_baal_sequence_to_dn_only(self) -> None:
        content = "\n".join(
            [
                "1\taliyn\taliyn/\tảlỉyn\tadj. m. sg. abs. nom.\tThe Very / Most Powerful\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN pl. cstr.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN sg.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. pl. cstr.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb G act. ptcpl. m. sg. abs. nom.\tto make\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 5)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1], "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN m. sg. abs. nom.\tBaʿlu/Baal\t"
            )
            self.assertEqual(len([line for line in lines if line.startswith("2\tbˤl\t")]), 1)


class SpacyYdkContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyYdkContextDisambiguator()

    def test_resolves_ydk_before_sgr(self) -> None:
        content = "\n".join(
            [
                "1\tydk\tyd(I)/+k\tyd (I)\tn. f.\thand\t",
                "1\tydk\tyd(II)/+k\tyd (II)\tn. m.\tlove\t",
                "2\tṣġr\tṣġr/\tṣġr\tadj.\tsmall\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "1\tydk\tyd(II)/+k=\tyd (II)\tn. m.\tlove\t")


if __name__ == "__main__":
    unittest.main()
