"""Tests for inferable morphology validation in the linter."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterFeatureValidationTest(unittest.TestCase):
    HEADER = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"

    def _lint_messages(self, body: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(self.HEADER + body, encoding="utf-8")
            issues = lint_file(
                path=path,
                dulat_forms={},
                entry_meta={},
                lemma_map={},
                entry_stems={},
                entry_gender={},
                udb_words=set(),
                baseline=None,
                input_format="auto",
                db_checks=False,
            )
            return [issue.message for issue in issues]

    def test_errors_when_prefixed_verb_pos_omits_person_gender_number(self) -> None:
        messages = self._lint_messages("1\ttmḫṣ\t!t=!mḫṣ[\t/m-ḫ-ṣ/\tvb G prefc.\tto wound\t\n")
        self.assertIn("Verb POS is missing explicit morphology from analysis: 2 m. sg.", messages)

    def test_errors_when_suffix_conjugation_pos_omits_plural(self) -> None:
        messages = self._lint_messages("1\tytn\tytn[:w\t/y-t-n/\tvb G suffc. 3 m. sg.\tto give\t\n")
        self.assertIn("Verb POS is missing explicit morphology from analysis: pl.", messages)

    def test_errors_when_nominal_pos_omits_construct(self) -> None:
        messages = self._lint_messages("1\tipdk\tipd/+k\tỉpd\tn. m.\ttunic\t\n")
        self.assertIn("Nominal POS is missing explicit morphology from analysis: cstr.", messages)

    def test_errors_when_feminine_plural_markers_are_omitted(self) -> None:
        messages = self._lint_messages("1\tggt\tgg/t=\tgg\tn.\troofs\t\n")
        self.assertIn("Nominal POS is missing explicit morphology from analysis: f. pl.", messages)

    def test_errors_when_t_split_conflicts_with_plural_pos(self) -> None:
        messages = self._lint_messages("1\tġrt\tġr(t(I)/t\tġrt (I)\tn. f. pl. cstr. gen.\trock\t\n")
        self.assertIn(
            "Nominal POS conflicts with analysis: '/t' marks feminine singular but POS is plural",
            messages,
        )

    def test_errors_when_t_equals_split_conflicts_with_singular_pos(self) -> None:
        messages = self._lint_messages(
            "1\tġrt\tġr(t(I)/t=\tġrt (I)\tn. f. sg. cstr. gen.\trock\t\n"
        )
        self.assertIn(
            "Nominal POS conflicts with analysis: '/t=' marks feminine plural but POS is singular",
            messages,
        )

    def test_does_not_require_feminine_marker_for_singular_t_split(self) -> None:
        messages = self._lint_messages(
            "1\tˤšrt\tˤšr(I)/t\tʕšr(t) (I)\tn. m. sg. cstr. nom.\tbanquet\t\n"
        )
        self.assertNotIn(
            "Nominal POS is missing explicit morphology from analysis: f.",
            messages,
        )


if __name__ == "__main__":
    unittest.main()
