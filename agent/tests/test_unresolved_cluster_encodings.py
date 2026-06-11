"""Encodings for the dominant unresolved-token clusters.

Source: the 642 '?'+hint rows after the end-of-pipeline gate. Two rules:
- verbs with weak/assimilating first radical (y/n/l/w) hide it with '('
  (ttn -> !t!(ytn[, dˤ -> (ydˤ[, tdd -> !t!(ndd[), per Tagging conventions;
- nominal surfaces are aligned against the lexeme letters with (/& marks
  (bht -> b&ht/, mat -> m(i&at/, ˤqšr -> (a&ˤqšr/, rpum -> rpu/m).
"""

import unittest

from scripts.refine_results_mentions import Entry, analysis_for_entry


def _entry(lemma: str, pos: str) -> Entry:
    return Entry(
        entry_id=1,
        lemma=lemma,
        hom="",
        pos=pos,
        gloss="",
        wiki_tr="",
        stem_glosses={},
        redirect_targets=(),
    )


class HiddenInitialWeakRadicalTest(unittest.TestCase):
    def test_prefixed_forms(self) -> None:
        cases = (
            ("ttn", "/y-t-n/", "!t!(ytn["),
            ("tdˤ", "/y-d-ʕ/", "!t!(ydˤ["),
            ("tdd", "/n-d-d/", "!t!(ndd["),
            ("ntn", "/y-t-n/", "!n!(ytn["),
        )
        for surface, lemma, expected in cases:
            analysis = analysis_for_entry(surface, _entry(lemma, "vb"), morph_values=["G, prefc."])
            self.assertEqual(analysis, expected, surface)

    def test_unprefixed_imperatives(self) -> None:
        cases = (
            ("dˤ", "/y-d-ʕ/", "(ydˤ["),
            ("rd", "/y-r-d/", "(yrd["),
            ("tn", "/y-t-n/", "(ytn["),
        )
        for surface, lemma, expected in cases:
            analysis = analysis_for_entry(surface, _entry(lemma, "vb"), morph_values=["G, impv."])
            self.assertEqual(analysis, expected, surface)

    def test_strong_roots_are_not_affected(self) -> None:
        analysis = analysis_for_entry("tmḫṣ", _entry("/m-ḫ-ṣ/", "vb"), morph_values=["G, prefc."])
        self.assertEqual(analysis, "!t!mḫṣ[")


class NominalAlignmentTest(unittest.TestCase):
    def test_inserted_surface_letter(self) -> None:
        analysis = analysis_for_entry("bht", _entry("bt (II)", "n."))
        self.assertEqual(analysis, "b&ht/")

    def test_vowel_substitution(self) -> None:
        analysis = analysis_for_entry("mat", _entry("mỉt", "n."))
        self.assertEqual(analysis, "m(i&at/")

    def test_initial_substitution(self) -> None:
        analysis = analysis_for_entry("ˤqšr", _entry("ảqšr", "n."))
        self.assertEqual(analysis, "(a&ˤqšr/")

    def test_trailing_plural_material_goes_after_closure(self) -> None:
        analysis = analysis_for_entry("rpum", _entry("rpủ", "n."))
        self.assertEqual(analysis, "rpu/m")

    def test_distant_surfaces_are_not_aligned(self) -> None:
        # No forced alignment when most letters differ.
        analysis = analysis_for_entry("ḫbtd", _entry("bt (II)", "n."))
        self.assertNotIn("&", analysis)


if __name__ == "__main__":
    unittest.main()
