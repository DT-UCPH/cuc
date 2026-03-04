"""Equivalence tests for the integrated spaCy-based offering context step."""

import tempfile
import unittest
from pathlib import Path

from pipeline.offering_context_step_factory import build_legacy_offering_context_steps
from pipeline.steps.spacy_offering_context import SpacyOfferingContextDisambiguator


def _run_steps(path: Path, steps) -> str:
    for step in steps:
        step.refine_file(path)
    return path.read_text(encoding="utf-8")


class SpacyOfferingContextDisambiguatorTest(unittest.TestCase):
    def _assert_equivalent(self, content: str, file_name: str = "KTU 1.test.tsv") -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            legacy_path = Path(tmp_dir) / file_name
            spacy_path = Path(tmp_dir) / f"spacy-{file_name}"
            legacy_path.write_text(content, encoding="utf-8")
            spacy_path.write_text(content, encoding="utf-8")

            legacy_output = _run_steps(legacy_path, build_legacy_offering_context_steps())
            spacy_output = _run_steps(spacy_path, [SpacyOfferingContextDisambiguator()])

            self.assertEqual(spacy_output, legacy_output)

    def test_matches_legacy_step_for_offering_sequence(self) -> None:
        content = "\n".join(
            [
                "#---- KTU 1.119 1",
                "154176	gdlt	gdl(I)/t=	gdlt (I)	n. f.	head of cattle",
                (
                    "154177	l	l(I);l(II);l(III)	l (I);l (II);l (III)"
                    "	prep.;adv.;functor	to;no;certainly"
                ),
                "154178	bˤlm	bˤl(II)/m	bʕl (II)	n. m.	lord",
                "",
            ]
        )
        self._assert_equivalent(content)

    def test_matches_legacy_step_for_non_offering_context(self) -> None:
        content = "\n".join(
            [
                "#---- KTU 1.1 1",
                "135588	ḥẓr	ḥẓr/	ḥẓr	n. m.	mansion",
                (
                    "135589	l	l(I);l(II);l(III)	l (I);l (II);l (III)"
                    "	prep.;adv.;functor	to;no;certainly"
                ),
                "135590	pˤn	pˤn/	pʕn	n. f.	foot",
                "",
            ]
        )
        self._assert_equivalent(content)


if __name__ == "__main__":
    unittest.main()
