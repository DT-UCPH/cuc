"""Regression tests for l(II) negation context linting."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file

L_NEGATION_MSG = "l(II) ('no/not') should be used only before verbal forms"
L_NEGATION_FORCED_MSG = "DULAT exception context requires a single l(II) reading"


class LinterLNegationContextTest(unittest.TestCase):
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

    def test_warns_when_l2_precedes_nonverb(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu/Baal\t\n"
            )
        )
        self.assertIn(L_NEGATION_MSG, msgs)

    def test_no_warning_when_l2_precedes_verb(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tytn\t!y!(ytn[\t/y-t-n/\tvb\tto give\t\n"
            )
        )
        self.assertNotIn(L_NEGATION_MSG, msgs)

    def test_exception_ref_requires_single_l2(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.3 IV:5\n"
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu/Baal\t\n"
            )
        )
        self.assertIn(L_NEGATION_FORCED_MSG, msgs)
        self.assertNotIn(L_NEGATION_MSG, msgs)

    def test_exception_ref_single_l2_is_accepted(self) -> None:
        msgs = self._lint_messages(
            (
                "# KTU 1.3 IV:5\n"
                "1\tl\tl(II)\tl (II)\tadv.\tno\t\n"
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu/Baal\t\n"
            )
        )
        self.assertNotIn(L_NEGATION_FORCED_MSG, msgs)
        self.assertNotIn(L_NEGATION_MSG, msgs)


if __name__ == "__main__":
    unittest.main()
