"""Tests for weak-initial verb analysis normalization."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.weak_verb import WeakVerbFixer


class WeakVerbFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = WeakVerbFixer()

    def test_adds_hidden_initial_l_to_prefixed_form(self) -> None:
        row = TabletRow("1", "yqḥ", "lqḥ[", "/l-q-ḥ/", "vb G prefc.", "to get hold of", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!(lqḥ[")

    def test_adds_hidden_initial_l_to_aleph_prefixed_form(self) -> None:
        row = TabletRow("1", "iqḥ", "lqḥ[", "/l-q-ḥ/", "vb G prefc.", "to get hold of", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!(ʔ&i!(lqḥ[")

    def test_adds_hidden_initial_l_to_nonprefixed_form(self) -> None:
        row = TabletRow("1", "qḥ", "lqḥ[", "/l-q-ḥ/", "vb G impv. 2", "to get hold of", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!(lqḥ[")

    def test_adds_imperative_marker_to_nonprefixed_infinitive_form(self) -> None:
        row = TabletRow("1", "qḥ", "lqḥ[/", "/l-q-ḥ/", "vb G inf.", "to get hold of", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!(lqḥ[/")

    def test_adds_imperative_marker_to_already_reconstructed_nonprefixed_form(self) -> None:
        row = TabletRow("1", "qḥ", "(lqḥ[", "/l-q-ḥ/", "vb G impv. 2", "to get hold of", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!!(lqḥ[")

    def test_normalizes_marked_l_prefixed_variant(self) -> None:
        row = TabletRow("1", "yqḥ", "!y!lqḥ[", "/l-q-ḥ/", "vb G prefc.", "to get hold of", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!(lqḥ[")

    def test_keeps_non_reconstructable_l_initial_variant(self) -> None:
        row = TabletRow(
            "1",
            "tlu",
            "lʔy(II)[",
            "/l-ʔ-y/w/ (II)",
            "vb G prefc.",
            "to lose strength",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "lʔy(II)[")


if __name__ == "__main__":
    unittest.main()
