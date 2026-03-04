"""File-level tests for the integrated spaCy-based `l`-context step."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.spacy_l_context import SpacyLContextDisambiguator


class SpacyLContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyLContextDisambiguator()

    def test_forces_l_ii_for_reference_exception(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 IV:5\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\tkeep me\n"
            "1\tl\tl(II)\tl (II)\tadv.\tno\tprefer me\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tdrop me\n"
            "2\tib\tib(I)/\tỉb (I)\tn. m. sg.\tenemy\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "1\tl\tl(II)\tl (II)\tadv.\tno\tprefer me")

    def test_resolves_l_kbd_compound(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 III:16\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\tfrom l\n"
            "2\tkbd\tkbd(I)/\tkbd (I)\tn.\tliver\tfrom noun\n"
            "2\tkbd\tkbd[\t/k-b-d/\tvb\tto honour\tfrom verb\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\tfrom l", lines)
            self.assertIn("2\tkbd\tkbd(I)/\tkbd (I)\tn.\twithin\tfrom noun", lines)
