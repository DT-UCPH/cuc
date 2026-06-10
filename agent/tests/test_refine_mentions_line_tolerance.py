"""Line-shift tolerance for reverse-mention lookups.

Regression source: DULAT citations for KTU 1.5 col. IV are consistently one
line lower than the CUC numbering (DULAT IV:n = CUC IV:n+1), so exact-line
lookups silently miss every mention in that column.
"""

import unittest

from scripts.refine_results_mentions import mentions_for_ref


class MentionsForRefTest(unittest.TestCase):
    REVERSE = {
        "CAT 1.5 IV:2": {4422},
        "CAT 1.5 IV:3": {3638},
        "CAT 1.5 III:9": {1397, 3882},
    }

    def test_exact_match_wins_and_is_not_diluted(self) -> None:
        self.assertEqual(mentions_for_ref(self.REVERSE, "CAT 1.5 IV:2"), {4422})

    def test_adjacent_line_fallback_when_exact_is_empty(self) -> None:
        # CUC IV:4 has no mentions of its own; DULAT cites the same words
        # under IV:3 (one-line shift).
        self.assertEqual(mentions_for_ref(self.REVERSE, "CAT 1.5 IV:4"), {3638})

    def test_fallback_unions_both_neighbours(self) -> None:
        self.assertEqual(mentions_for_ref(self.REVERSE, "CAT 1.5 IV:1"), {4422})
        # IV:3 exact match exists, so neighbours are ignored.
        self.assertEqual(mentions_for_ref(self.REVERSE, "CAT 1.5 IV:3"), {3638})

    def test_zero_tolerance_disables_fallback(self) -> None:
        self.assertEqual(mentions_for_ref(self.REVERSE, "CAT 1.5 IV:4", line_tolerance=0), set())

    def test_unparseable_ref_returns_exact_only(self) -> None:
        self.assertEqual(mentions_for_ref(self.REVERSE, ""), set())
        self.assertEqual(mentions_for_ref(self.REVERSE, "CAT 1.5"), set())


if __name__ == "__main__":
    unittest.main()
