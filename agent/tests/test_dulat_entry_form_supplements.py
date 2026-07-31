"""Tests for supplementing DULAT entries whose cached `forms` rows are missing."""

import unittest

from pipeline.config.dulat_entry_form_supplements import (
    ENTRY_FORM_SUPPLEMENTS,
    supplemental_forms,
)


class DulatEntryFormSupplementsTest(unittest.TestCase):
    def test_athtart_dn_has_a_supplemental_form(self) -> None:
        """ʕṯtrt (I) is the goddess; without a form the toponym (II) wins unopposed."""
        self.assertEqual(supplemental_forms("ʕṯtrt", "I"), (("ʕṯtrt", ""),))

    def test_lookup_normalises_ayin_and_homonym_case(self) -> None:
        self.assertEqual(supplemental_forms("ʿṯtrt", "i"), (("ʕṯtrt", ""),))
        self.assertEqual(supplemental_forms("ˤṯtrt", "I"), (("ʕṯtrt", ""),))

    def test_unlisted_entries_get_nothing(self) -> None:
        self.assertEqual(supplemental_forms("ʕṯtrt", "II"), ())
        self.assertEqual(supplemental_forms("bʕl", "II"), ())
        self.assertEqual(supplemental_forms("", ""), ())

    def test_keys_are_normalised_at_module_load(self) -> None:
        for lemma, hom in ENTRY_FORM_SUPPLEMENTS:
            self.assertEqual(lemma, lemma.strip())
            self.assertNotIn("ʿ", lemma)
            self.assertNotIn("ˤ", lemma)
            self.assertEqual(hom, hom.upper())


if __name__ == "__main__":
    unittest.main()
