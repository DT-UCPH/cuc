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

    def test_forces_genitive_on_single_nominal_after_preposition(self) -> None:
        doc = self._doc_from_lines(
            "1\tb\tb\tb\tprep.\tin\t",
            "2\tṣpn\tṣpn/\tṣpn\tTN/DN m. sg. abs. nom.\tṢapānu/Zaphon\t",
            "2\tṣpn\tṣpn/\tṣpn\tTN/DN m. sg. cstr. nom.\tṢapānu/Zaphon\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["TN/DN m. sg. abs. gen."],
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

    def test_forces_construct_chain_after_preposition(self) -> None:
        doc = self._doc_from_lines(
            "1\tb\tb\tb\tprep.\tin\t",
            "2\tnpš\tnpš(I)/\tnpš (I)\tn. f. sg. abs. nom.\tthroat\t",
            "3\tbn\tbn(I)/\tbn (I)\tn. m. sg. abs. nom.\tson\t",
            "4\tilm\til(I)/m\tỉl (I)\tn. m. pl. abs. nom.\tgod\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["n. f. sg. cstr. gen."],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[2]._.resolved_candidates],
            ["n. m. sg. cstr. gen."],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[3]._.resolved_candidates],
            ["n. m. pl. abs. gen."],
        )

    def test_forces_construct_chain_without_preposition(self) -> None:
        doc = self._doc_from_lines(
            "1\tbn\tbn(I)/\tbn (I)\tn. m. sg. abs. nom.\tson\t",
            "2\tilm\til(I)/m\tỉl (I)\tn. m. pl. abs. nom.\tgod\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[0]._.resolved_candidates],
            ["n. m. sg. cstr. nom."],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["n. m. pl. abs. gen."],
        )

    def test_suffix_bearing_nominals_do_not_form_construct_chain_heads(self) -> None:
        doc = self._doc_from_lines(
            "1\tˤṣk\tˤṣ/+k\tʕṣ\tn. m. sg. cstr. nom.\ttree\t",
            "2\tˤbṣk\tˤbṣ(I)/+k\tʕbṣ (I)\tn. m. sg. cstr. nom.\tmace\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[0]._.resolved_candidates],
            ["n. m. sg. cstr. nom."],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["n. m. sg. cstr. nom."],
        )

    def test_suffix_bearing_nominal_after_preposition_stays_construct(self) -> None:
        doc = self._doc_from_lines(
            "1\tb\tb\tb\tprep.\tin\t",
            "2\tˤbṣk\tˤbṣ(I)/+k\tʕbṣ (I)\tn. m. sg. cstr. nom.\tmace\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["n. m. sg. cstr. gen."],
        )

    def test_preposition_with_suffix_does_not_force_next_nominal_genitive(self) -> None:
        doc = self._doc_from_lines(
            "1\tˤmy\tˤm(I)+y\tʕm (I)\tprep.\tto\t",
            "2\tpˤnk\tpˤn/+k\tpʕn\tn. f. cstr. nom.\tfoot\t",
            "2\tpˤnk\tpˤn/+k\tpʕn\tn. f. cstr. gen.\tfoot\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["n. f. cstr. nom.", "n. f. cstr. gen."],
        )

    def test_prunes_suffix_conjugation_to_second_singular_after_at_pronoun(self) -> None:
        doc = self._doc_from_lines(
            "1\tat\tat(I)\tảt (I)\tpers. pn.\tyou\t",
            "2\typˤt\typˤ[t===\t/y-p-ʕ/\tvb G suffc. 3 f. sg.\tto go up\t",
            "2\typˤt\t(]n]ypˤ[t===\t/y-p-ʕ/\tvb N suffc. 3 f. sg.\tto go up\t",
            "2\typˤt\typˤ[t=\t/y-p-ʕ/\tvb G suffc. 2 m. sg.\tto go up\t",
            "2\typˤt\t(]n]ypˤ[t=\t/y-p-ʕ/\tvb N suffc. 2 m. sg.\tto go up\t",
            "2\typˤt\typˤ[t==\t/y-p-ʕ/\tvb G suffc. 2 f. sg.\tto go up\t",
            "2\typˤt\t(]n]ypˤ[t==\t/y-p-ʕ/\tvb N suffc. 2 f. sg.\tto go up\t",
            "2\typˤt\typˤ[t\t/y-p-ʕ/\tvb G suffc. 1 c. sg.\tto go up\t",
            "2\typˤt\t(]n]ypˤ[t\t/y-p-ʕ/\tvb N suffc. 1 c. sg.\tto go up\t",
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            [
                "vb G suffc. 2 m. sg.",
                "vb N suffc. 2 m. sg.",
                "vb G suffc. 2 f. sg.",
                "vb N suffc. 2 f. sg.",
            ],
        )


if __name__ == "__main__":
    unittest.main()
