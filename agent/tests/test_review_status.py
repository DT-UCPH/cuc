"""Regression tests for review-status handling of editorial damage."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".agents/skills/review-automatic-parsing/scripts/review_status.py"
)
SPEC = importlib.util.spec_from_file_location("review_status", SCRIPT)
assert SPEC and SPEC.loader
review_status = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_status)


class ReviewStatusBrokenSurfaceTest(unittest.TestCase):
    def test_sign_span_damage_makes_public_comment_unnecessary(self) -> None:
        self.assertTrue(review_status.is_broken("r", "r[   ]"))
        self.assertTrue(review_status.is_broken("mš", "m[   ]š"))
        self.assertTrue(review_status.is_broken("tmtt", "<t>mtt"))
        self.assertTrue(review_status.is_broken("dbḥ", "{dbḥ}"))

    def test_undamaged_legible_surface_still_needs_reason(self) -> None:
        self.assertFalse(review_status.is_broken("nl", "nl"))
        self.assertFalse(review_status.is_broken("amḫṣ", "amḫṣ"))

    def test_automatic_rows_retain_surface_only_fallback(self) -> None:
        self.assertTrue(review_status.is_broken("xxx"))
        self.assertFalse(review_status.is_broken("nl"))


if __name__ == "__main__":
    unittest.main()
