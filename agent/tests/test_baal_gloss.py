"""Tests for final Baal gloss normalization."""

import unittest

from pipeline.steps.baal_gloss import BaalGlossFixer
from pipeline.steps.base import TabletRow


class BaalGlossFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = BaalGlossFixer()

    def test_rewrites_baal_common_noun_gloss_to_lord(self) -> None:
        row = TabletRow(
            "1",
            "bˤly",
            "bˤl(II)/+y",
            "bʕl (II)",
            "n. m. sg. cstr. gen.",
            "Baʿlu/Baal",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.gloss, "lord")

    def test_leaves_unsuffixed_baal_dn_gloss_untouched(self) -> None:
        row = TabletRow(
            "2",
            "bˤl",
            "bˤl(II)/",
            "bʕl (II)",
            "DN m. sg. abs. nom.",
            "Baʿlu",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result, row)

    def test_leaves_unsuffixed_baal_noun_gloss_untouched(self) -> None:
        row = TabletRow(
            "3",
            "bˤl",
            "bˤl(II)/",
            "bʕl (II)",
            "n. m. pl. abs. gen.",
            "Baʿlu/Baal",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result, row)

    def test_leaves_mixed_baal_pos_untouched(self) -> None:
        row = TabletRow(
            "4",
            "bˤly",
            "bˤl(II)/+y",
            "bʕl (II)",
            "n. m./DN",
            "Baʿlu",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result, row)


if __name__ == "__main__":
    unittest.main()
