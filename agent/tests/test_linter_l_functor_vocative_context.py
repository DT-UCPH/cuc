"""Regression tests for l(III)/l(IV) context linting."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterLFunctorVocativeContextTest(unittest.TestCase):
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

    def test_warns_when_l3_reference_is_not_single_l3(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.24:36\n"
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tảbnm\tảbn/m\tảbn\tn. m.\tstones\t\n"
            )
        )
        self.assertIn("DULAT context requires a single l(III) reading", msgs)

    def test_no_warning_when_l3_reference_has_single_l3(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.24:36\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tảbnm\tảbn/m\tảbn\tn. m.\tstones\t\n"
            )
        )
        self.assertNotIn("DULAT context requires a single l(III) reading", msgs)

    def test_warns_when_l4_reference_is_not_single_l4(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.24:15\n"
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tkṯrt\tkṯrt/\tkṯrt\tDN\tKotharat\t\n"
            )
        )
        self.assertIn("DULAT context requires a single l(IV) reading", msgs)

    def test_does_not_warn_on_column_mismatch_reference(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.4 I:23\n"
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tksỉ\tksỉ/\tksỉ\tn. m.\tthrone\t\n"
            )
        )
        self.assertNotIn("DULAT context requires a single l(IV) reading", msgs)
        self.assertNotIn("DULAT context requires a single l(III) reading", msgs)

    def test_overlap_reference_uses_next_token_context(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.17 I:23\n"
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\ttbrknn\t!t!brkn[n\t/b-r-k/\tvb\tto bless\t\n"
                "3\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "3\tl\tl(IV)\tl (IV)\tinterj.\toh!\t\n"
                "4\tṯr\tṯr(I)/\tṯr (I)\tn. m.\tbull\t\n"
            )
        )
        self.assertIn("DULAT context requires a single l(III) reading", msgs)
        self.assertIn("DULAT context requires a single l(IV) reading", msgs)

    def test_l4_reference_before_verb_does_not_force_l4(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.24:15\n"
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\ttbʕ\t!t!bʕ[\t/t-b-ʕ/\tvb\tto go\t\n"
            )
        )
        self.assertNotIn("DULAT context requires a single l(IV) reading", msgs)


if __name__ == "__main__":
    unittest.main()
