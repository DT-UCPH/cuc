"""Tests for the III-ʔ case-ending aleph / labelled-case agreement check.

Complements ``analysis_has_missing_iii_aleph_case_encoding`` (which warns when
the ``(V/.../&X`` case encoding is absent): this check errors when the encoded
case vowel is *present* but contradicts the labelled case.  In a III-ʔ noun,
adjective, participle, or bound infinitive the word-final aleph grapheme spells
the case vowel (u=nom, i=gen, a=acc); see
lexicon_and_grammar/tagging_conventions_cuc.md and Notarius, *The Ugaritic
passive participle*, §2.2.2 criterion (4).
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import iii_aleph_case_mismatch, lint_file


class IiiAlephCaseAgreementHelperTest(unittest.TestCase):
    def test_genitive_aleph_labelled_nominative_mismatches(self) -> None:
        # The nši over-generation caught in auto_parsing/0.2.8.
        self.assertEqual(
            iii_aleph_case_mismatch("nš(ʔ[/&i", "vb G act. ptcpl. m. sg. abs. nom."),
            ("gen.", "nom."),
        )

    def test_accusative_aleph_labelled_accusative_is_consistent(self) -> None:
        self.assertIsNone(
            iii_aleph_case_mismatch("mr(u&i(I)/&a", "n. m. sg. abs. acc.")
        )

    def test_genitive_aleph_labelled_genitive_is_consistent(self) -> None:
        self.assertIsNone(
            iii_aleph_case_mismatch("mr(u(I)/&i", "n. m. sg. abs. gen.")
        )

    def test_nominative_aleph_labelled_nominative_is_consistent(self) -> None:
        self.assertIsNone(iii_aleph_case_mismatch("ks(u/&u", "n. m. sg. abs. nom."))

    def test_oblique_accepts_genitive_and_accusative(self) -> None:
        self.assertIsNone(
            iii_aleph_case_mismatch("mr(u(I)/&i", "n. m. sg. abs. gen., acc.")
        )
        self.assertIsNone(
            iii_aleph_case_mismatch("mr(u(I)/&a", "n. m. sg. abs. gen., acc.")
        )
        # nominative aleph is still incompatible with an oblique label.
        self.assertEqual(
            iii_aleph_case_mismatch("mr(u(I)/&u", "n. m. sg. abs. gen., acc."),
            ("nom.", "acc., gen."),
        )

    def test_case_ending_aleph_before_pronominal_suffix(self) -> None:
        self.assertEqual(
            iii_aleph_case_mismatch(
                "ks(u/&u+h", "n. m. sg. cstr. gen. + 3 m. sg. suff."
            ),
            ("nom.", "gen."),
        )

    def test_no_case_label_is_ignored(self) -> None:
        self.assertIsNone(iii_aleph_case_mismatch("mr(u(I)/&i", "adv."))

    def test_non_boundary_aleph_is_not_a_case_ending(self) -> None:
        # A realized aleph that is not right after the `/` boundary must not be
        # read as a case ending.
        self.assertIsNone(iii_aleph_case_mismatch("(ʔ&il/", "n. m. sg. abs. nom."))


class IiiAlephCaseAgreementLintFileTest(unittest.TestCase):
    def _lint(self, row: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.8"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                + row
                + "\n",
                encoding="utf-8",
            )
            return lint_file(
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

    def test_mislabelled_case_is_flagged_as_error(self) -> None:
        issues = self._lint(
            "1\tnši\tnš(ʔ[/&i\t/n-š-ʔ/\tvb G act. ptcpl. m. sg. abs. nom.\tto lift\t"
        )
        matches = [i for i in issues if i.message.startswith("III-ʔ case-ending aleph")]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].level, "error")

    def test_consistent_case_is_not_flagged(self) -> None:
        issues = self._lint(
            "1\tnši\tnš(ʔ[/&i\t/n-š-ʔ/\tvb G inf. cstr. gen.\tto lift\t"
        )
        matches = [i for i in issues if i.message.startswith("III-ʔ case-ending aleph")]
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
