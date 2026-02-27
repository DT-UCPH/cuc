"""Regression tests for `k(III)` forcing in target verb-leading bigrams."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterKFunctorBigramContextTest(unittest.TestCase):
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

    def test_warns_when_k_before_target_verb_is_ambiguous(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
                "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
                "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t\n"
            )
        )
        self.assertIn(
            "Formula bigram `k yṣḥ` should use a single k(III) reading",
            msgs,
        )

    def test_no_warning_when_k_before_target_verb_is_single_k_iii(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
                "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t\n"
            )
        )
        self.assertNotIn(
            "Formula bigram `k yṣḥ` should use a single k(III) reading",
            msgs,
        )

    def test_no_warning_for_non_target_next_surface(self) -> None:
        msgs = self._lint_messages(
            (
                "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t\n"
                "1\tk\tk(I)\tk (I)\tprep.\tlike\t\n"
                "2\tilm\til(I)/m\tỉl (I)\tn. m.\tgod\t\n"
            )
        )
        self.assertNotIn(
            "Formula bigram `k ilm` should use a single k(III) reading",
            msgs,
        )


if __name__ == "__main__":
    unittest.main()
