"""Verb encodings for assimilated Š-augment and realized aleph radicals.

Conventions agreed in review:
- Š of ṯ-initial roots assimilates the augment to ṯ; encode the hidden š as
  a substitution: ṯṯb -> ](š&ṯ]ṯb[ (DULAT /ṯ-b/: Š prefc. tṯṯb, yṯṯb,
  tṯṯbn; impv. ṯṯb; inf. ṯṯb).
- Aleph radicals realized as vowel letters follow the (ʔ&V pattern in any
  position: likt -> l(ʔ&ik[t, iḫdn -> (ʔ&iḫd[n, tnšan -> !t!nš(ʔ&a[n.
"""

import unittest

from scripts.refine_results_mentions import Entry, analysis_for_entry


def _verb(lemma: str) -> Entry:
    return Entry(
        entry_id=1,
        lemma=lemma,
        hom="",
        pos="vb",
        gloss="",
        wiki_tr="",
        stem_glosses={},
        redirect_targets=(),
    )


class SStemAssimilationTest(unittest.TestCase):
    def test_impv_and_inf_surface(self) -> None:
        analysis = analysis_for_entry("ṯṯb", _verb("/ṯ-b/"), morph_values=["Š, impv."])
        self.assertEqual(analysis, "](š&ṯ]ṯb[")

    def test_prefixed_surface(self) -> None:
        analysis = analysis_for_entry("tṯṯb", _verb("/ṯ-b/"), morph_values=["Š, prefc."])
        self.assertEqual(analysis, "!t!](š&ṯ]ṯb[")

    def test_prefixed_surface_with_ending(self) -> None:
        analysis = analysis_for_entry("tṯṯbn", _verb("/ṯ-b/"), morph_values=["Š, prefc."])
        self.assertEqual(analysis, "!t!](š&ṯ]ṯb[n")


class AlephRealizationTest(unittest.TestCase):
    def test_ii_aleph_suffix_conjugation(self) -> None:
        analysis = analysis_for_entry("likt", _verb("/l-ʔ-k/"), morph_values=["G, suffc."])
        self.assertEqual(analysis, "l(ʔ&ik[t")

    def test_i_aleph_unprefixed(self) -> None:
        analysis = analysis_for_entry("iḫdn", _verb("/ʔ-ḫ-d(/ḏ)/"), morph_values=["G, impv."])
        self.assertEqual(analysis, "(ʔ&iḫd[n")

    def test_iii_aleph_with_visible_initial_n(self) -> None:
        # Vocalization after '[' per conventions; the written n stays visible
        # (contrast tša -> !t!(nš(ʔ[&a where the n is elided on the tablet).
        analysis = analysis_for_entry("tnšan", _verb("/n-š-ʔ/"), morph_values=["G, prefc."])
        self.assertEqual(analysis, "!t!nš(ʔ[&an")

    def test_elided_initial_n_stays_hidden(self) -> None:
        analysis = analysis_for_entry("tša", _verb("/n-š-ʔ/"), morph_values=["G, prefc."])
        self.assertEqual(analysis, "!t!(nš(ʔ[&a")

    def test_n_suffix_iii_aleph_with_visible_formative(self) -> None:
        analysis = analysis_for_entry("nḫtu", _verb("/ḫ-t-ʔ/"), morph_values=["N, suffc."])
        self.assertEqual(analysis, "]n]ḫt(ʔ[&u")

    def test_unmatched_aleph_root_fallback_marks_reconstructed_aleph(self) -> None:
        analysis = analysis_for_entry("mmlat", _verb("/m-l-ʔ/"))
        self.assertEqual(analysis, "ml(ʔ[")


if __name__ == "__main__":
    unittest.main()
