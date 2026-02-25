"""Tests for l(II) exception reference matching."""

import unittest

from pipeline.config.l_negation_exception_refs import (
    extract_separator_ref,
    is_forced_l_negation_ref,
)


class LNegationExceptionRefsTest(unittest.TestCase):
    def test_extracts_separator_ref(self) -> None:
        self.assertEqual(extract_separator_ref("# KTU 1.3 IV:5"), "KTU 1.3 IV:5")

    def test_forces_ktu_1_3_iv_5(self) -> None:
        self.assertTrue(is_forced_l_negation_ref("KTU 1.3 IV:5"))

    def test_forces_ktu_4_348_1(self) -> None:
        self.assertTrue(is_forced_l_negation_ref("KTU 4.348:1"))

    def test_forces_ktu_4_213_range(self) -> None:
        self.assertTrue(is_forced_l_negation_ref("KTU 4.213:2"))
        self.assertTrue(is_forced_l_negation_ref("KTU 4.213:23"))
        self.assertFalse(is_forced_l_negation_ref("KTU 4.213:24"))

    def test_forces_when_range_overlaps_exception_window(self) -> None:
        self.assertTrue(is_forced_l_negation_ref("KTU 4.213:2-23"))
        self.assertTrue(is_forced_l_negation_ref("CAT 4.213:1-5"))
        self.assertFalse(is_forced_l_negation_ref("KTU 4.213:24-28"))


if __name__ == "__main__":
    unittest.main()
