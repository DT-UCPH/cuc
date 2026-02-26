"""Regression tests for `l + kbd` compound-preposition linting."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterLKbdCompoundPrepTest(unittest.TestCase):
    def _lint_messages(self, body: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n" + body,
                encoding="utf-8",
            )
            issues = lint_file(
                path=path,
                dulat_forms={},
                entry_meta={},
                lemma_map={},
                entry_stems={},
                entry_gender={},
                udb_words=None,
                baseline=None,
                input_format="auto",
                db_checks=False,
            )
            return [issue.message for issue in issues]

    def test_warns_when_l_kbd_is_not_collapsed_to_compound_prep(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tkbd\tkbd(I)/\tkbd (I)\tn.\tliver\t\n"
                "2\tkbd\tkbd(II)/\tkbd (II)\tn. m.\ttotal (quantity or price)\t\n"
                "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
            )
        )
        self.assertIn(
            "Compound preposition `l kbd` should use single readings: l(I) and "
            "kbd(I) with POS `n.` and gloss `within`",
            msgs,
        )

    def test_no_warning_when_l_kbd_is_normalized(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "2\tkbd\tkbd(I)/\tkbd (I)\tn.\twithin\t\n"
                "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
            )
        )
        self.assertNotIn(
            "Compound preposition `l kbd` should use single readings: l(I) and "
            "kbd(I) with POS `n.` and gloss `within`",
            msgs,
        )

    def test_no_warning_when_kbd_i_is_unavailable(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tkbd\tkbd(II)/\tkbd (II)\tn. m.\ttotal (quantity or price)\t\n"
                "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
            )
        )
        self.assertNotIn(
            "Compound preposition `l kbd` should use single readings: l(I) and "
            "kbd(I) with POS `n.` and gloss `within`",
            msgs,
        )


if __name__ == "__main__":
    unittest.main()
