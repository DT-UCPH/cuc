"""Regression tests for `l + body-part` compound-preposition linting."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterLBodyCompoundPrepTest(unittest.TestCase):
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

    def test_warns_when_l_paan_is_not_normalized(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tpˤn\tpˤn/\tpʕn\tn. f.\tfoot\t\n"
                "3\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
            )
        )
        self.assertIn(
            "Compound preposition `l pˤn` should use single readings: l(I) and pˤn/ "
            "with POS `n. f.` and gloss `at the feet of`",
            msgs,
        )

    def test_no_warning_when_l_paan_is_normalized(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "2\tpˤn\tpˤn/\tpʕn\tn. f.\tat the feet of\t\n"
                "3\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
            )
        )
        self.assertNotIn(
            "Compound preposition `l pˤn` should use single readings: l(I) and pˤn/ "
            "with POS `n. f.` and gloss `at the feet of`",
            msgs,
        )

    def test_warns_when_l_zaar_is_not_normalized(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tẓr\tẓr(I)/\tẓr (I)\tn. m.\tback\t\n"
                "3\tqdqdh\tqdqd/h\tqdqd\tn. m.\tskull\t\n"
            )
        )
        self.assertIn(
            "Compound preposition `l ẓr` should use single readings: l(I) and ẓr(I)/ "
            "with POS `n. m.` and gloss `upon`",
            msgs,
        )


if __name__ == "__main__":
    unittest.main()
