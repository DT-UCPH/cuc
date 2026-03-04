"""Equivalence tests for the integrated spaCy-based formula context step."""

import tempfile
import unittest
from pathlib import Path

from pipeline.formula_context_step_factory import build_legacy_formula_context_steps
from pipeline.steps.spacy_formula_context import SpacyFormulaContextDisambiguator


def _run_steps(path: Path, steps) -> str:
    for step in steps:
        step.refine_file(path)
    return path.read_text(encoding="utf-8")


class SpacyFormulaContextDisambiguatorTest(unittest.TestCase):
    def _assert_equivalent(self, content: str, file_name: str = "KTU 1.test.tsv") -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            legacy_path = Path(tmp_dir) / file_name
            spacy_path = Path(tmp_dir) / f"spacy-{file_name}"
            legacy_path.write_text(content, encoding="utf-8")
            spacy_path.write_text(content, encoding="utf-8")

            legacy_output = _run_steps(legacy_path, build_legacy_formula_context_steps())
            spacy_output = _run_steps(spacy_path, [SpacyFormulaContextDisambiguator()])

            self.assertEqual(spacy_output, legacy_output)

    def test_matches_legacy_chain_for_bigram_formula(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\taliyn\taliyn/\tảlỉyn\tadj. m.\tThe Very / Most Powerful\tkeep\n"
            "2\tbˤl\tbˤl(II)/;bˤl[\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\tkeep\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_chain_for_trigram_formula(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tidk\tidk\tỉdk\tnarrative adv. functor\tthen\t\n"
            "2\tl\tl(I);l(II);l(III)\tl (I);l (II);l (III)\tprep.;adv.;functor\tto;no;certainly\t\n"
            "3\tttn\tytn[\t/y-t-n/\tvb\tto give\t\n"
            "4\tpnm\tpn(m/m\tpnm\tn. m. pl. tant.\tface\t\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_chain_for_single_variant_trigram(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\trbt\trb(t(I)/t\trbt (I)\tn. f.\tLady\t\n"
            "2\taṯrt\taṯrt(II)/\tảṯrt (II)\tDN\tAsherah\t\n"
            "3\tym\tym(II)/\tym (II)\tn. m.\tsea\t\n"
        )
        self._assert_equivalent(content)


if __name__ == "__main__":
    unittest.main()
