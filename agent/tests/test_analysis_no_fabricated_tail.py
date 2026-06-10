"""The verb renderer must not fabricate tails from unmatched surface letters.

Regression source (Elijah, KTU 2.16:64 and 2.38:23): when the surface does
not start with the stem, the renderer appended the surface's trailing
letters after '[' (ṯṯb -> ]š]ṯb[b, tṯṯb -> ]š]ṯb[ṯb), creating analyses
that are wrong by construction.
"""

import unittest

from scripts.refine_results_mentions import Entry, analysis_for_entry


def _verb_entry(lemma: str) -> Entry:
    return Entry(
        entry_id=1,
        lemma=lemma,
        hom="",
        pos="vb",
        gloss="to send back",
        wiki_tr="",
        stem_glosses={},
        redirect_targets=(),
    )


class AnalysisNoFabricatedTailTest(unittest.TestCase):
    def test_surface_not_starting_with_stem_gets_no_tail(self) -> None:
        analysis = analysis_for_entry("ṯṯb", _verb_entry("/ṯ-b/"), morph_values=["Š, impv."])
        self.assertEqual(analysis, "]š]ṯb[")

    def test_prefixed_surface_not_matching_stem_gets_no_tail(self) -> None:
        analysis = analysis_for_entry("tṯṯb", _verb_entry("/ṯ-b/"), morph_values=["Š, prefc."])
        self.assertNotIn("[ṯb", analysis)

    def test_valid_suffix_tail_is_preserved(self) -> None:
        # Surface starts with the stem: the remainder is a genuine ending.
        analysis = analysis_for_entry("ṯbt", _verb_entry("/ṯ-b/"), morph_values=["G, suffc."])
        self.assertEqual(analysis, "ṯb[t")


if __name__ == "__main__":
    unittest.main()
