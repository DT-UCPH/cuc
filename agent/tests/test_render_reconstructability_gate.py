"""Render-time gate: never emit an analysis that cannot reconstruct.

Regression source: yddll -> dll[:d (KTU 1.10x). When no candidate encoding
reconstructs the surface, the row must fall back to '?' with the DULAT
candidates preserved as a comment hint for the reviewer.
"""

import unittest

from scripts.refine_results_mentions import analysis_reconstructs, gate_rendered_variants


class AnalysisReconstructsTest(unittest.TestCase):
    def test_sound_and_unsound_analyses(self) -> None:
        self.assertTrue(analysis_reconstructs("likt", "l(ʔ&ik[t"))
        self.assertTrue(analysis_reconstructs("tṯṯb", "!t!](š&ṯ]ṯb["))
        self.assertFalse(analysis_reconstructs("yddll", "dll[:d"))
        self.assertFalse(analysis_reconstructs("gh", "ytn["))


class GateRenderedVariantsTest(unittest.TestCase):
    def test_unsound_variants_are_dropped_when_sound_exist(self) -> None:
        rendered = [
            ("ytn[", "/y-t-n/", "vb", "to give"),
            ("g/+h", "g", "n. m. sg.", "(loud) voice"),
        ]
        kept, hint = gate_rendered_variants("gh", rendered)
        self.assertEqual(kept, [("g/+h", "g", "n. m. sg.", "(loud) voice")])
        self.assertIsNone(hint)

    def test_all_unsound_yields_hint(self) -> None:
        rendered = [("dll[:d", "/d-l-l/", "vb D prefc.", "to oppress, subdue")]
        kept, hint = gate_rendered_variants("yddll", rendered)
        self.assertEqual(kept, [])
        self.assertIn("/d-l-l/", hint)
        self.assertIn("to oppress", hint)

    def test_broken_surfaces_are_not_gated(self) -> None:
        rendered = [("dll[:d", "/d-l-l/", "vb", "to oppress")]
        kept, hint = gate_rendered_variants("ydxll", rendered)
        self.assertEqual(kept, rendered)
        self.assertIsNone(hint)


if __name__ == "__main__":
    unittest.main()
