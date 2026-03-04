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
