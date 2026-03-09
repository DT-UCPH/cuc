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

    def test_rewrites_journey_formula_ytn_and_pnm_after_plural_subject(self) -> None:
        doc = self._doc_from_lines(
            "1\tilm\til(I)/m\tỉl (I)\tn. m. pl. abs. gen.\tgod\t",
            "2\tidk\tidk\tỉdk\tnarrative adv. functor\tthen\t",
            "3\tl\tl(I)\tl (I)\tprep.\tto\t",
            "3\tl\tl(II)\tl (II)\tadv.\tno\t",
            "3\tl\tl(III)\tl (III)\tfunctor\tcertainly\t",
            "4\tytn\t!y!(ytn[\t/y-t-n/\tvb G prefc. 3 m. sg.\tto give\t",
            "4\tytn\tytn[\t/y-t-n/\tvb G suffc. 3 m. sg.\tto give\t",
            "5\tpnm\tpn(m/m\tpnm\tn. m. pl. tant. abs. nom.\tface\t",
        )
        self.assertEqual(
            [candidate.dulat for candidate in doc[2]._.resolved_candidates],
            ["l (III)"],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[3]._.resolved_candidates],
            ["vb G prefc. 3 m. pl.", "vb G suffc. 3 m. pl."],
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[4]._.resolved_candidates],
            ["pn(m/m"],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[4]._.resolved_candidates],
            ["n. m. pl. tant. abs. acc."],
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

    def test_epistolary_rgm_opening_builds_infinitive_from_letter_formula(self) -> None:
        doc = self._doc_from_lines(
            "1\ttḥm\ttḥm/\ttḥm\tn. m. sg. cstr. nom.\tmessage\t",
            "2\tl\tl(I)\tl (I)\tprep.\tto\t",
            "2\tplsy\tplsy/\tplsy\tPN sg. cstr. gen.\tplsy\t",
            "3\trgm\trgm[/\t/r-g-m/\tvb G pass. ptcpl. m. sg. abs. gen.\tto say\t",
            "3\trgm\trgm/\trgm\tn. m. sg. abs. gen.\tword\t",
            "4\tyšlm\t!y!šlm[\t/š-l-m/\tvb G prefc. 3 m. sg.\tto be well\t",
            "4\tyšlm\t!y!šlm[:d\t/š-l-m/\tvb D prefc. 3 m. sg.\tto be well\t",
            source_name="KTU 2.10.tsv",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[3]._.resolved_candidates],
            ["!!rgm[/"],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[3]._.resolved_candidates],
            ["vb G inf."],
        )

    def test_epistolary_rgm_later_prefers_noun(self) -> None:
        doc = self._doc_from_lines(
            "1\ttḥm\ttḥm/\ttḥm\tn. m. sg. abs. nom.\tmessage\t",
            "2\trgm\t!!rgm[/\t/r-g-m/\tvb G inf.\tto say\t",
            "2\trgm\trgm/\trgm\tn. m. sg. abs. nom.\tword\t",
            "3\tyšlm\t!y!šlm[\t/š-l-m/\tvb G prefc. 3 m. sg.\tto be well\t",
            "4\tmnm\tmnm\tmnm\tindef. pn.\tany(thing)\t",
            "5\trgm\trgm[/\t/r-g-m/\tvb G pass. ptcpl. m. sg. abs. gen.\tto say\t",
            "5\trgm\trgm/\trgm\tn. m. sg. abs. gen.\tword\t",
            source_name="KTU 2.38.tsv",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[4]._.resolved_candidates],
            ["rgm/"],
        )
        self.assertEqual(
            [candidate.dulat for candidate in doc[4]._.resolved_candidates],
            ["rgm"],
        )

    def test_non_epistolary_rgm_is_unchanged(self) -> None:
        doc = self._doc_from_lines(
            "1\trgm\trgm[/\t/r-g-m/\tvb G pass. ptcpl. m. sg. abs. nom.\tto say\t",
            "1\trgm\trgm/\trgm\tn. m. sg. abs. nom.\tword\t",
            "2\tmlk\tmlk(II)/\tmlk (II)\tn. m. sg. abs. nom.\tkingdom (power and territory)\t",
            source_name="KTU 1.3.tsv",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["rgm[/", "rgm/"],
        )

    def test_non_epistolary_rgm_after_pronoun_builds_imperative(self) -> None:
        doc = self._doc_from_lines(
            "1\thyt\thy&t\thy\tpers. pn.\tshe\t",
            "2\tw\tw\tw\tconj.\tand\t",
            "3\trgm\trgm[\t/r-g-m/\tvb G suffc. 3 m. sg.\tto say\t",
            "3\trgm\trgm[\t/r-g-m/\tvb G impv. 2\tto say\t",
            "3\trgm\t!!rgm[/\t/r-g-m/\tvb G inf.\tto say\t",
            "3\trgm\trgm/\trgm\tn. m. sg. abs. nom.\tword\t",
            "4\tl\tl(I)\tl (I)\tprep.\tto\t",
            "5\tbtlt\tbtl(t/t\tbtlt\tn. f. sg. cstr. gen.\tvirgin\t",
            source_name="KTU 1.3.tsv",
        )

        self.assertEqual(
            [candidate.analysis for candidate in doc[2]._.resolved_candidates],
            ["!!rgm["],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[2]._.resolved_candidates],
            ["vb G impv. 2"],
        )

    def test_non_epistolary_rgm_dm_message_formula_prefers_noun(self) -> None:
        doc = self._doc_from_lines(
            "1\tdm\tdm(I)\tdm (I)\tfunctor\tsince\t",
            "2\trgm\trgm[\t/r-g-m/\tvb G suffc. 3 m. sg.\tto say\t",
            "2\trgm\trgm[\t/r-g-m/\tvb G impv. 2\tto say\t",
            "2\trgm\t!!rgm[/\t/r-g-m/\tvb G inf.\tto say\t",
            "2\trgm\trgm[/\t/r-g-m/\tvb G pass. ptcpl. m. sg. abs. nom.\tto say\t",
            "2\trgm\trgm/\trgm\tn. m. sg. abs. nom.\tword\t",
            "3\tiṯ\tiṯ(I)/\tỉṯ (I)\tn. m. sg. abs. nom.\tpresence\t",
            source_name="KTU 1.3.tsv",
        )

        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["rgm/"],
        )

    def test_builds_kbd_d_imperative_before_personal_pronoun(self) -> None:
        doc = self._doc_from_lines(
            "1\tw\tw\tw\tconj.\tand\t",
            "2\tkbd\tkbd(II)/\tkbd (II)\tn. m. sg. abs. nom.\ttotal (quantity or price)\t",
            "3\thyt\thy&t\thy\tpers. pn.\tshe\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["kbd[:d"],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["vb D impv. 2"],
        )
        self.assertEqual(
            [candidate.dulat for candidate in doc[1]._.resolved_candidates],
            ["/k-b-d/"],
        )

    def test_leaves_kbd_nominal_without_following_pronoun(self) -> None:
        doc = self._doc_from_lines(
            "1\tkbd\tkbd(II)/\tkbd (II)\tn. m. sg. abs. nom.\ttotal (quantity or price)\t",
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN m. sg. abs. nom.\tBaʿlu/Baal\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["kbd(II)/"],
        )

    def test_builds_kbd_d_imperative_for_hwt_surface_fallback(self) -> None:
        doc = self._doc_from_lines(
            "1\tw\tw\tw\tconj.\tand\t",
            "2\tkbd\tkbd(II)/\tkbd (II)\tn. m. sg. abs. nom.\ttotal (quantity or price)\t",
            "3\thwt\thw(t(I)/t\thwt (I)\tn. f. sg. abs. gen.\tword\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["kbd[:d"],
        )

    def test_letter_blessing_pair_prefers_prefixed_suffix_forms(self) -> None:
        doc = self._doc_from_lines(
            "1\tilm\til(I)/m\tỉl (I)\tn. m. pl.\tgod\t",
            "2\ttġrk\tnġr[k\t/n-ġ-r/\tvb G prefc.\tto protect\t",
            "2\ttġrk\tnġr[k\t/n-ġ-r/\tvb G suffc.\tto protect\t",
            "3\ttšlmk\t!t!šlm[k:d\t/š-l-m/\tvb D prefc.\tto be well\t",
            "3\ttšlmk\ttšlmk[\t/š-l-m/\tvb D suffc. 3 m. sg.\tto be well\t",
            source_name="KTU 2.38.tsv",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["!t!(nġr[+k"],
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[2]._.resolved_candidates],
            ["!t!šlm[:d+k"],
        )

    def test_letter_blessing_pair_supports_plural_suffix(self) -> None:
        doc = self._doc_from_lines(
            "1\tšlm\tšlm(I)/\tšlm (I)\tn. m. sg. abs. nom.\tpeace\t",
            "2\ttġrkm\tnġr[k\t/n-ġ-r/\tvb G prefc.\tto protect\t",
            "2\ttġrkm\tnġr[k\t/n-ġ-r/\tvb G suffc.\tto protect\t",
            "3\ttšlmkm\t!t!šlm[k:d\t/š-l-m/\tvb D prefc.\tto be well\t",
            "3\ttšlmkm\ttšlmkm[\t/š-l-m/\tvb D suffc. 3 m. pl.\tto be well\t",
            source_name="KTU 2.85.tsv",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["!t!(nġr[+km"],
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[2]._.resolved_candidates],
            ["!t!šlm[:d+km"],
        )

    def test_letter_blessing_handles_reversed_order(self) -> None:
        doc = self._doc_from_lines(
            "1\tilm\til(I)/m\tỉl (I)\tn. m. pl.\tgod\t",
            "2\ttšlmk\t!t!šlm[k:d\t/š-l-m/\tvb D prefc.\tto be well\t",
            "2\ttšlmk\ttšlmk[\t/š-l-m/\tvb D suffc. 3 m. sg.\tto be well\t",
            "3\ttġrk\tnġr[k\t/n-ġ-r/\tvb G prefc.\tto protect\t",
            "3\ttġrk\tnġr[k\t/n-ġ-r/\tvb G suffc.\tto protect\t",
            source_name="KTU 2.4.tsv",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["!t!šlm[:d+k"],
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[2]._.resolved_candidates],
            ["!t!(nġr[+k"],
        )

    def test_epistolary_bare_shlm_prunes_d_suffix_and_adjective_noise(self) -> None:
        doc = self._doc_from_lines(
            "1\thnny\thn+ny\thn\tfunctor\tbehold!\t",
            "2\tˤmn\tˤm(I)+n\tʕm (I)\tprep.\tto\t",
            "3\tšlm\tšlm(I)/\tšlm (I)\tn. m. sg. abs. nom.\tpeace\t",
            "3\tšlm\tšlm[\t/š-l-m/\tvb G suffc. 3 m. sg.\tto be well\t",
            "3\tšlm\tšlm[:d\t/š-l-m/\tvb D suffc. 3 m. sg.\tto be well\t",
            "3\tšlm\tšlm[:d:w\t/š-l-m/\tvb D suffc. 3 m. pl.\tto be well\t",
            "3\tšlm\tšlm(III)/\tšlm (III)\tadj. m. sg. abs. nom.\tpure\t",
            "4\tṯmny\tṯm+ny\tṯm\tadv.\tthere\t",
            source_name="KTU 2.38.tsv",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[2]._.resolved_candidates],
            ["šlm(I)/", "šlm["],
        )


if __name__ == "__main__":
    unittest.main()
