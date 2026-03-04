"""Equivalence tests for the integrated spaCy-based `l`-context step."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.l_context_step_factory import build_legacy_l_context_steps
from pipeline.steps.spacy_l_context import SpacyLContextDisambiguator


def _run_steps(path: Path, step_factories) -> str:
    for step in step_factories:
        step.refine_file(path)
    return path.read_text(encoding="utf-8")


class SpacyLContextDisambiguatorTest(unittest.TestCase):
    def _assert_equivalent(self, content: str, file_name: str = "KTU 1.test.tsv") -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            legacy_path = Path(tmp_dir) / file_name
            spacy_path = Path(tmp_dir) / f"spacy-{file_name}"
            legacy_path.write_text(content, encoding="utf-8")
            spacy_path.write_text(content, encoding="utf-8")

            legacy_output = _run_steps(legacy_path, build_legacy_l_context_steps())
            spacy_output = _run_steps(spacy_path, [SpacyLContextDisambiguator()])

            self.assertEqual(spacy_output, legacy_output)

    def test_matches_legacy_chain_for_forced_l_ii_reference(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 IV:5\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\tkeep me\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\tprefer me\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tdrop me\n"
            "2\tib\tib(I)/\tỉb (I)\tn. m. sg.\tenemy\t\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_chain_for_functor_vocative_overlap(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.17 I:23\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\ttbrknn\t!t!brkn[n\t/b-r-k/\tvb\tto bless\t\n"
            "3\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "3\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "4\tṯr\tṯr(I)/\tṯr (I)\tn. m.\tbull\t\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_chain_for_l_kbd_compound(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 III:16\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tfrom l\n"
            "2\tkbd\tkbd(I)/\tkbd (I)\tn.\tliver\tfrom noun\n"
            "2\tkbd\tkbd[\t/k-b-d/\tvb\tto honour\tfrom verb\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_chain_for_body_compound(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\tcomment\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tother\n"
            "2\tpˤn\tpˤn/\tpʕn\tn. f.\tfoot\tnote\n"
            "3\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_chain_for_pn_preposition_payload(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tkeep comment\n"
            "2\tpnh\tpn/(m+h=\tpn\tfunctor\tlest\tkeep pnh comment\n"
        )
        self._assert_equivalent(content)

    def test_matches_legacy_chain_for_baal_outside_ktu4(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m./DN\tBaʿlu/Baal\tprefer dn\n"
            "2\tbˤl\tbˤl[\t/b-ʕ-l/\tvb\tto make\tdrop verb\n"
        )
        self._assert_equivalent(content, file_name="KTU 1.baal.tsv")


if __name__ == "__main__":
    unittest.main()
