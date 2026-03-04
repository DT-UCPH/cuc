"""Equivalence tests for the integrated spaCy-based `k`-context step."""

import tempfile
import unittest
from pathlib import Path

from pipeline.k_context_step_factory import build_legacy_k_context_steps
from pipeline.steps.spacy_k_context import SpacyKContextDisambiguator


def _run_steps(path: Path, steps) -> str:
    for step in steps:
        step.refine_file(path)
    return path.read_text(encoding="utf-8")


class SpacyKContextDisambiguatorTest(unittest.TestCase):
    def _assert_equivalent(self, content: str, file_name: str = "KTU 1.test.tsv") -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            legacy_path = Path(tmp_dir) / file_name
            spacy_path = Path(tmp_dir) / f"spacy-{file_name}"
            legacy_path.write_text(content, encoding="utf-8")
            spacy_path.write_text(content, encoding="utf-8")

            legacy_output = _run_steps(legacy_path, build_legacy_k_context_steps())
            spacy_output = _run_steps(spacy_path, [SpacyKContextDisambiguator()])

            self.assertEqual(spacy_output, legacy_output)

    def test_matches_legacy_step_for_target_verb_bigram(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\t+k\t-k (I)\t\t\tplus\n"
            "1\tk\t~k\t-k (II)\t\t\tclitic\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\tprep\n"
            "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_step_when_k_iii_variant_already_exists(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\tkeep me\n"
            "1\tk\tk(II)\tk (II)\temph. functor\tyes\tdrop me\n"
            "2\tyraš\t!y!raš[\t/r-š/\tvb\tto desire\t\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_step_when_next_surface_is_nonverbal(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
            "2\tyṣḥ\tyṣḥ/\tyṣḥ\tn. m.\tshout\t\n"
        )
        self._assert_equivalent(content)


if __name__ == "__main__":
    unittest.main()
