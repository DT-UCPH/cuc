"""POS-string grammar checks.

Regression source: reviewed/auto rows carried malformed POS strings such as
`vb G impv. 2` (dangling person digit) and `n. f. pl. tant. pl.` (duplicate
number token) that passed the linter silently.
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file, pos_grammar_problems


class PosGrammarProblemsTest(unittest.TestCase):
    def test_dangling_person_digit_is_flagged(self) -> None:
        problems = pos_grammar_problems("vb G impv. 2")
        self.assertTrue(any("person" in p for p in problems))

    def test_duplicate_number_token_is_flagged(self) -> None:
        problems = pos_grammar_problems("n. f. pl. tant. pl.")
        self.assertTrue(any("repeated" in p for p in problems))

    def test_well_formed_pos_strings_pass(self) -> None:
        for pos_value in (
            "vb G prefc. 3 m. sg.",
            "vb Gt prefc. 2 f. sg.",
            "vb D prefc. 3 f. sg. + 3 m. sg. suff.",
            "vb G impv. m. sg.",
            "vb G inf. abs.",
            "vb G act. ptcpl. m. sg. abs. acc.",
            "n. m. sg. abs. acc.",
            "n. f. pl. tant. abs. nom.",
            "n. m. pl./du. tant. abs. gen.",
            "n. num. f. sg.",
            "pers. pn. 1 c. sg.",
            "DN m. sg. abs. nom.",
            "prep. + 2 m. sg. suff.",
            "det. or rel. functor",
            "narrative adv. functor",
            "?",
            "",
        ):
            self.assertEqual(pos_grammar_problems(pos_value), [], pos_value)


class LinterPosGrammarIntegrationTest(unittest.TestCase):
    def test_garbled_pos_row_is_warning(self) -> None:
        header = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
        rows = (
            "1\trgm\t!!rgm[\t/r-g-m/\tvb G impv. 2\tto say\t\n"
            "2\thmlt\thml(t/t=\thmlt\tn. f. pl. tant. pl.\tmultitude\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.7"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(header + rows, encoding="utf-8")
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
        hits = [(x.level, x.line_id) for x in issues if x.message.startswith("POS grammar")]
        self.assertEqual(sorted(hits), [("warning", "1"), ("warning", "2")])


if __name__ == "__main__":
    unittest.main()
