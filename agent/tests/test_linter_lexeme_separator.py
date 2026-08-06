"""Regression tests for the '|' lexeme separator.

DULAT uses ',' between synonyms and ';' between non-synonyms inside a single
gloss, so neither can delimit anything of ours. A multi-lexeme row separates its
lexemes with '|', and a gloss keeps DULAT's own punctuation intact.
"""

import unittest

from linter.lint import has_semicolon_packed_variants, split_csv_field


class SplitCsvFieldTest(unittest.TestCase):
    def test_pipe_separates_lexemes(self) -> None:
        self.assertEqual(split_csv_field("k (II) | ḏd (III)"), ["k (II)", "ḏd (III)"])

    def test_dulat_comma_inside_one_gloss_is_not_a_separator(self) -> None:
        """'flock, herd' is DULAT's gloss for ḏd (III) — one item, not two."""
        self.assertEqual(split_csv_field("yes | flock, herd"), ["yes", "flock, herd"])

    def test_single_lexeme_is_one_item(self) -> None:
        self.assertEqual(split_csv_field("behold!; look!; thus"), ["behold!; look!; thus"])

    def test_legacy_comma_rows_still_split(self) -> None:
        """Rows written before the convention separate with ',' and must keep working."""
        self.assertEqual(split_csv_field("k (I), rks"), ["k (I)", "rks"])

    def test_empty(self) -> None:
        self.assertEqual(split_csv_field(""), [])
        self.assertEqual(split_csv_field(None), [])


class SemicolonPackedVariantsTest(unittest.TestCase):
    @staticmethod
    def _row(analysis="x/", dulat="x", pos="n. m. sg.", gloss="thing"):
        return ["1", "x", analysis, dulat, pos, gloss, ""]

    def test_gloss_semicolons_are_not_packed_variants(self) -> None:
        """DULAT's own non-synonym punctuation must not read as packed options."""
        self.assertFalse(
            has_semicolon_packed_variants(self._row(gloss="behold!; look!; thus"))
        )

    def test_packed_analysis_is_still_reported(self) -> None:
        self.assertTrue(has_semicolon_packed_variants(self._row(analysis="x/; y/")))

    def test_packed_pos_is_still_reported(self) -> None:
        self.assertTrue(has_semicolon_packed_variants(self._row(pos="n. m. sg.; adj.")))

    def test_clean_row(self) -> None:
        self.assertFalse(has_semicolon_packed_variants(self._row()))


if __name__ == "__main__":
    unittest.main()
