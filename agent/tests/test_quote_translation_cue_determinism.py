"""The DULAT-quote resolver's cue word must be deterministic.

`_candidate_cues` iterates the gloss words; `_translation_words` returns a
frozenset whose iteration order is hash-seed-dependent, and the chosen cue
(`cues[0]`) surfaces in the `DULAT quote in ... (cue: X)` comment. The words
must be sorted so the note is reproducible across runs.
"""

import unittest

from spacy_ugaritic.components.quote_translation_context import _candidate_cues
from spacy_ugaritic.types import Candidate


class CandidateCueDeterminismTest(unittest.TestCase):
    def _cand(self, gloss: str) -> Candidate:
        return Candidate(analysis="", dulat="", pos="", gloss=gloss)

    def test_cues_are_sorted(self) -> None:
        cues = _candidate_cues(self._cand("(head of) cattle"))
        self.assertEqual(cues, ("cattle", "head"))
        # The surfaced cue (cues[0]) is the alphabetically-first content word.
        self.assertEqual(cues[0], "cattle")

    def test_order_is_stable_regardless_of_input_phrasing(self) -> None:
        a = _candidate_cues(self._cand("head of cattle"))
        b = _candidate_cues(self._cand("cattle, head"))
        self.assertEqual(a, b)

    def test_stopwords_and_short_words_excluded(self) -> None:
        # "of" is a stopword; sorting must not reintroduce it.
        self.assertNotIn("of", _candidate_cues(self._cand("(head of) cattle")))


if __name__ == "__main__":
    unittest.main()
