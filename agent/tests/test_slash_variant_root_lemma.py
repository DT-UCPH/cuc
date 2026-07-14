"""Slash-alternative radicals in root lemmas (/y/w-ḥ-l/).

Regression source (Elijah, KTU 2.16:44): twḥln was parsed as !t!(y[wḥln
because lemma_to_letters('/y/w-ḥ-l/') collapsed the root to the single
letter 'y'. The slash separates alternative radicals of one slot; the
variant matching the surface must be chosen.
"""

import unittest

from scripts.refine_results_mentions import Entry, analysis_for_entry, lemma_to_letters


class SlashVariantRootLemmaTest(unittest.TestCase):
    def test_variant_matching_surface_is_chosen(self) -> None:
        self.assertEqual(lemma_to_letters("/y/w-ḥ-l/", fallback="twḥln"), "wḥl")

    def test_first_variant_is_default(self) -> None:
        self.assertEqual(lemma_to_letters("/y/w-ḥ-l/", fallback=""), "yḥl")

    def test_plain_roots_are_unchanged(self) -> None:
        self.assertEqual(lemma_to_letters("/m-ġ-y/", fallback="mġny"), "mġy")
        self.assertEqual(lemma_to_letters("/d-k(-k)/", fallback="dk"), "dk")

    def test_twḥln_renders_with_preformative_and_sound_root(self) -> None:
        entry = Entry(
            entry_id=4773,
            lemma="/y/w-ḥ-l/",
            hom="",
            pos="vb",
            gloss="to be worried",
            wiki_tr="",
            stem_glosses={},
            redirect_targets=(),
        )
        analysis = analysis_for_entry("twḥln", entry, morph_values=["G, prefc."])
        self.assertEqual(analysis, "!t!wḥl[n")


if __name__ == "__main__":
    unittest.main()
