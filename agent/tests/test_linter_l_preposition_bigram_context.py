"""Regression tests for high-confidence `l + X` prepositional bigram linting."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterLPrepositionBigramContextTest(unittest.TestCase):
    def _lint_messages(self, body: str, filename: str = "KTU 1.test.tsv") -> list[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / filename
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

    def test_warns_when_l_arsh_is_not_single_l_i(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
            )
        )
        self.assertIn("Bigram `l arṣ` should use a single l(I) reading", msgs)

    def test_warns_when_l_baal_outside_ktu4_is_not_collapsed(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m./DN\tBaʿlu/Baal\t\n"
                "2\tbˤl\tbˤl[\t/b-ʕ-l/\tvb\tto make\t\n"
            )
        )
        self.assertIn(
            "Outside KTU 4.*, `l bˤl` should use single readings: l(I) and bˤl(II)",
            msgs,
        )

    def test_no_warning_for_l_baal_in_ktu4(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m./DN\tBaʿlu/Baal\t\n"
                "2\tbˤl\tbˤl[\t/b-ʕ-l/\tvb\tto make\t\n"
            ),
            filename="KTU 4.test.tsv",
        )
        self.assertNotIn(
            "Outside KTU 4.*, `l bˤl` should use single readings: l(I) and bˤl(II)",
            msgs,
        )

    def test_warns_when_l_pn_is_not_canonical_prep(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
                "2\tpn\tpn(m/\tpnm\tn. m. pl. tant.\tface\t\n"
                "2\tpn\tpn\tpn\tfunctor\tlest\t\n"
            )
        )
        self.assertIn(
            "Lexicalized preposition `l pn` should use single readings: l(I) and pn(m/ "
            "with POS `n. m. pl. tant.` and gloss `in front`",
            msgs,
        )

    def test_no_warning_when_l_pn_is_canonical_prep(self) -> None:
        msgs = self._lint_messages(
            ("1\tl\tl(I)\tl (I)\tprep.\tto\t\n2\tpn\tpn(m/\tpnm\tn. m. pl. tant.\tin front\t\n")
        )
        self.assertNotIn(
            "Lexicalized preposition `l pn` should use single readings: l(I) and pn(m/ "
            "with POS `n. m. pl. tant.` and gloss `in front`",
            msgs,
        )


if __name__ == "__main__":
    unittest.main()
