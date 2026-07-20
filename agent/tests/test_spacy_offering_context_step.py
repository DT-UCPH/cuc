"""File-level tests for the integrated spaCy-based offering context step."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_offering_context import SpacyOfferingContextDisambiguator


class SpacyOfferingContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyOfferingContextDisambiguator()

    def test_resolves_l_in_offering_sequence(self) -> None:
        content = "\n".join(
            [
                "#---- KTU 1.119 1",
                "154176\tgdlt\tgdl(I)/t=\tgdlt (I)\tn. f.\thead of cattle",
                (
                    "154177\tl\tl(I);l(II);l(III)\tl (I);l (II);l (III)"
                    "\tprep.;adv.;functor\tto;no;certainly"
                ),
                "154178\tbˤlm\tbˤl(II)/m\tbʕl (II)\tn. m.\tlord",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "154177\tl\tl(I)\tl (I)\tprep.\tto\t")


if __name__ == "__main__":
    unittest.main()
