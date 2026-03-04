"""File-level tests for the integrated spaCy-based `k`-context step."""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_k_context import SpacyKContextDisambiguator


class SpacyKContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyKContextDisambiguator()

    def test_forces_k_iii_before_target_verb_bigram(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\t+k\t-k (I)\t\t\tplus\n"
            "1\tk\t~k\t-k (II)\t\t\tclitic\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\tprep\n"
            "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\tplus",
                lines,
            )


if __name__ == "__main__":
    unittest.main()
