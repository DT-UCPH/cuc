"""Regression tests for the published/internal split of the comment column.

Everything before a '##' is published to users of the corpus; everything after
it is addressed to the project and stripped before release. The linter has a
much older rule that treats '#' in a raw row as an inline-comment delimiter,
which would otherwise truncate the row's fields at the '##' and tear the
internal note out of its column.
"""

import unittest

from linter.lint import comment_marker_problems, split_inline_comment


class SplitInlineCommentTest(unittest.TestCase):
    def test_double_hash_is_not_an_inline_comment(self) -> None:
        raw = "1\tmdl\tmdl(I)/\tmdl (I)\tn.\tharness\tnote ## internal"
        core, comment = split_inline_comment(raw)
        self.assertEqual(core, raw)
        self.assertEqual(comment, "")

    def test_wholly_internal_comment_stays_in_its_column(self) -> None:
        raw = "1\tx\tx/\tx\tn.\tthing\t## Migrated from legacy reviewed tokenization."
        core, comment = split_inline_comment(raw)
        self.assertTrue(core.endswith("## Migrated from legacy reviewed tokenization."))
        self.assertEqual(comment, "")

    def test_single_hash_still_splits(self) -> None:
        """The legacy inline-comment form must keep working."""
        core, comment = split_inline_comment("1\tx\tx/\t# legacy note")
        self.assertEqual(core, "1\tx\tx/")
        self.assertEqual(comment, "legacy note")

    def test_no_hash(self) -> None:
        self.assertEqual(split_inline_comment("1\tx\tx/"), ("1\tx\tx/", ""))


class CommentMarkerProblemsTest(unittest.TestCase):
    def test_leading_single_hash_is_reported(self) -> None:
        self.assertTrue(comment_marker_problems("# if šmm is dual"))

    def test_leading_double_hash_is_allowed(self) -> None:
        """A comment may be wholly internal."""
        self.assertEqual(comment_marker_problems("## Migrated from legacy tokenization."), [])

    def test_published_then_internal_is_allowed(self) -> None:
        self.assertEqual(comment_marker_problems("DULAT cites x here. ## needs a wider pass"), [])

    def test_second_marker_is_reported(self) -> None:
        problems = comment_marker_problems("a ## b ## c")
        self.assertTrue(any("more than one" in p for p in problems))

    def test_empty_internal_section_is_reported(self) -> None:
        problems = comment_marker_problems("something ##")
        self.assertTrue(any("empty" in p for p in problems))

    def test_ordinary_comment_is_clean(self) -> None:
        self.assertEqual(comment_marker_problems("k ˤṣr 'like a bird'."), [])

    def test_empty(self) -> None:
        self.assertEqual(comment_marker_problems(""), [])
        self.assertEqual(comment_marker_problems(None), [])


if __name__ == "__main__":
    unittest.main()
