"""Tests for reference matcher of `l(III)`/`l(IV)` disambiguation."""

import unittest

from pipeline.config.l_functor_vocative_refs import (
    canonical_ktu_ref_key,
    expected_l_homonym_for_ref,
)


class LFunctorVocativeRefsTest(unittest.TestCase):
    def test_canonicalizes_with_or_without_column(self) -> None:
        self.assertEqual(canonical_ktu_ref_key("KTU 1.17 VI:42"), "1.17 VI:42")
        self.assertEqual(canonical_ktu_ref_key("KTU 1.17:42"), "1.17:42")
        self.assertEqual(canonical_ktu_ref_key("KTU 1.24 15"), "1.24:15")

    def test_returns_none_for_non_parsable_reference(self) -> None:
        self.assertIsNone(canonical_ktu_ref_key("KTU 1.19"))

    def test_preserves_column_to_avoid_cross_column_collisions(self) -> None:
        self.assertEqual(canonical_ktu_ref_key("KTU 1.4 I:23"), "1.4 I:23")
        self.assertEqual(canonical_ktu_ref_key("KTU 1.4 VII:23"), "1.4 VII:23")
        self.assertNotEqual(
            canonical_ktu_ref_key("KTU 1.4 I:23"),
            canonical_ktu_ref_key("KTU 1.4 VII:23"),
        )
        self.assertIsNone(expected_l_homonym_for_ref("KTU 1.4 I:23", next_has_verb=False))
        self.assertEqual(expected_l_homonym_for_ref("KTU 1.4 VII:23", next_has_verb=False), "IV")

    def test_forces_l3_in_l3_only_reference(self) -> None:
        self.assertEqual(expected_l_homonym_for_ref("KTU 1.24:36", next_has_verb=False), "III")
        self.assertEqual(expected_l_homonym_for_ref("KTU 1.24:36", next_has_verb=True), "III")

    def test_forces_l4_in_l4_reference_when_next_is_nonverbal(self) -> None:
        self.assertEqual(expected_l_homonym_for_ref("KTU 1.24:15", next_has_verb=False), "IV")

    def test_does_not_force_l4_when_next_is_verbal(self) -> None:
        self.assertIsNone(expected_l_homonym_for_ref("KTU 1.24:15", next_has_verb=True))

    def test_uses_next_verb_to_resolve_overlapping_l3_l4_ref(self) -> None:
        self.assertEqual(expected_l_homonym_for_ref("KTU 1.17 I:23", next_has_verb=True), "III")
        self.assertEqual(expected_l_homonym_for_ref("KTU 1.17 I:23", next_has_verb=False), "IV")


if __name__ == "__main__":
    unittest.main()
