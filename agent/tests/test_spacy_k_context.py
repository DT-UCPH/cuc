"""Focused tests for the spaCy-based `k`-context component."""

import unittest

from spacy_ugaritic.doc_builder import build_doc, group_tablet_lines
from spacy_ugaritic.language import create_ugaritic_k_context_nlp


class SpacyKContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_k_context_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.3.tsv"):
        grouped = group_tablet_lines(lines)
        doc = build_doc(self.nlp, grouped, source_name=source_name)
        return self.nlp(doc)

    def test_forces_k_iii_before_target_verb_bigram(self) -> None:
        doc = self._doc_from_lines(
            "1\tk\t+k\t-k (I)\t\t\t",
            "1\tk\t~k\t-k (II)\t\t\t",
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t",
            "2\tyṣḥ\t!y!ṣḥ[\t/ṣ-ḥ/\tvb\tto exclaim\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["k(III)"])

    def test_skips_for_non_target_surface(self) -> None:
        doc = self._doc_from_lines(
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t",
            "2\tilm\til(I)/m\tỉl (I)\tn. m.\tgod\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["k(III)", "k(I)"])

    def test_skips_when_target_surface_is_nonverbal(self) -> None:
        doc = self._doc_from_lines(
            "1\tk\tk(III)\tk (III)\tSubordinating or completive functor\twhen\t",
            "1\tk\tk(I)\tk (I)\tprep.\tlike\t",
            "2\tyṣḥ\tyṣḥ/\tyṣḥ\tn. m.\tshout\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["k(III)", "k(I)"])


if __name__ == "__main__":
    unittest.main()
