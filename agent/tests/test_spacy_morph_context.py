"""Focused tests for the spaCy-based morphology-context component."""

import unittest

from spacy_ugaritic.doc_builder import build_doc, group_tablet_lines
from spacy_ugaritic.language import create_ugaritic_morph_context_nlp


class SpacyMorphContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_morph_context_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.5.tsv"):
        grouped = group_tablet_lines(lines)
        doc = build_doc(self.nlp, grouped, source_name=source_name)
        return self.nlp(doc)

    def test_prefers_plural_and_dual_third_masculine_before_plural_subject(self) -> None:
        doc = self._doc_from_lines(
            "1\ttṯkḥ\t!t!ṯkḥ[\t/ṯ-k-ḥ/\tvb G prefc. 3 f. sg.\tto burn\t",
            "1\ttṯkḥ\t!t=!ṯkḥ[\t/ṯ-k-ḥ/\tvb G prefc. 2 m. sg.\tto burn\t",
            "1\ttṯkḥ\t!t!ṯkḥ[\t/ṯ-k-ḥ/\tvb G prefc. 3 m. du.\tto burn\t",
            "1\ttṯkḥ\t!t!ṯkḥ[:w\t/ṯ-k-ḥ/\tvb G prefc. 3 m. pl.\tto burn\t",
            "2\tttrp\t!t!]t]rp(y[p:d:w\t/r-p-y/\tvb Dt prefc. 3 m. pl.\tto slacken\t",
            "3\tšmm\tšm(m(I)/m\tšmm (I)\tn. m. tant. pl. / n. m. tant. du.\theavens\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[0]._.resolved_candidates],
            ["vb G prefc. 3 m. du.", "vb G prefc. 3 m. pl."],
        )

    def test_leaves_token_unchanged_without_plural_dual_subject(self) -> None:
        doc = self._doc_from_lines(
            "1\ttmḫṣ\t!t!mḫṣ[\t/m-ḫ-ṣ/\tvb G prefc. 3 f. sg.\tto wound\t",
            "1\ttmḫṣ\t!t=!mḫṣ[\t/m-ḫ-ṣ/\tvb G prefc. 2 m. sg.\tto wound\t",
            "2\tltn\tltn(I)/\tltn (I)\tDN m.\tLeviathan\t",
        )
        self.assertEqual(len(doc[0]._.resolved_candidates), 2)

    def test_prefers_plural_candidate_from_previous_plural_subject(self) -> None:
        doc = self._doc_from_lines(
            "1\tilm\til(I)/m\tỉl (I)\tn. m. pl.\tgod\t",
            "2\tl\tl(I)\tl (I)\tprep.\tto\t",
            "3\tytn\t!y!(ytn[\t/y-t-n/\tvb G prefc. 3 m. sg.\tto give\t",
            "3\tytn\t!t!(ytn[:w\t/y-t-n/\tvb G prefc. 3 m. pl.\tto give\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[2]._.resolved_candidates],
            ["vb G prefc. 3 m. pl."],
        )

    def test_forces_genitive_on_nominal_after_preposition(self) -> None:
        doc = self._doc_from_lines(
            "1\tb\tb\tb\tprep.\tin\t",
            "2\tṣpn\tṣpn/\tṣpn\tTN/DN m. sg. abs. nom.\tṢapānu/Zaphon\t",
            "2\tṣpn\tṣpn/\tṣpn\tTN/DN m. sg. cstr. nom.\tṢapānu/Zaphon\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["TN/DN m. sg. abs. gen.", "TN/DN m. sg. cstr. gen."],
        )

    def test_forces_genitive_on_adjective_noun_phrase_after_preposition(self) -> None:
        doc = self._doc_from_lines(
            "1\tb\tb\tb\tprep.\tin\t",
            "2\taliyn\taliyn/\tảlỉyn\tadj. m. sg. abs. nom.\tThe Very / Most Powerful\t",
            "3\tbˤl\tbˤl(II)/\tbʕl (II)\tDN m. sg. abs. nom.\tBaʿlu/Baal\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["adj. m. sg. abs. gen."],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[2]._.resolved_candidates],
            ["DN m. sg. abs. gen."],
        )

    def test_forces_genitive_on_participle_after_preposition(self) -> None:
        doc = self._doc_from_lines(
            "1\tb\tb\tb\tprep.\tin\t",
            "2\tmḫṣ\tmḫṣ[/\t/m-ḫ-ṣ/\tvb G act. ptcpl. m. sg. abs. nom.\tto wound\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["vb G act. ptcpl. m. sg. abs. gen."],
        )


if __name__ == "__main__":
    unittest.main()
