"""Focused tests for the spaCy-based lexical context component."""

import unittest

from pipeline.dulat_attestation_index import DulatAttestationIndex, normalize_reference_label
from spacy_ugaritic.doc_builder import build_doc, parse_grouped_tokens
from spacy_ugaritic.language import (
    create_ugaritic_baal_context_nlp,
    create_ugaritic_ydk_context_nlp,
)


class SpacyBaalContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_baal_context_nlp()

    def _doc_from_lines(
        self,
        *lines: str,
        source_name: str = "KTU 1.3.tsv",
        attestation_index: DulatAttestationIndex | None = None,
    ):
        tokens = parse_grouped_tokens(lines)
        doc = build_doc(self.nlp, tokens, source_name=source_name)
        doc.user_data["attestation_index"] = attestation_index or DulatAttestationIndex.empty()
        return self.nlp(doc)

    def test_prunes_baal_labourer_and_normalizes_verbal_variant_outside_ktu4(self) -> None:
        doc = self._doc_from_lines(
            (
                "1\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\tbʕl (II);bʕl (I);/b-ʕ-l/"
                "\tn. m./DN;n. m.;vb\tBaʿlu;labourer;to make\t"
            ),
        )
        self.assertEqual(doc[0]._.resolved_candidates[0].analysis, "bˤl(II)/;bˤl[/")

    def test_collapses_mixed_baal_plural(self) -> None:
        doc = self._doc_from_lines(
            "1	bˤlm	bˤl(II)/;bˤl(I)/m	bʕl (II);bʕl (I)	n. m./DN;n. m.	Baʿlu;labourer	",
        )
        self.assertEqual(doc[0]._.resolved_candidates[0].analysis, "bˤl(II)/m")
        self.assertEqual(doc[0]._.resolved_candidates[0].gloss, "lord")

    def test_collapses_aliyn_baal_to_divine_name(self) -> None:
        doc = self._doc_from_lines(
            "1\taliyn\taliyn/\tảlỉyn\tadj. m. sg. abs. nom.\tThe Very / Most Powerful\t",
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN pl. cstr.\tBaʿlu/Baal\t",
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN sg.\tBaʿlu/Baal\t",
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. pl. cstr.\tBaʿlu/Baal\t",
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg.\tBaʿlu/Baal\t",
            "2\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb G act. ptcpl. m. sg. abs. nom.\tto make\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["bˤl(II)/"],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["DN m. sg. abs. nom."],
        )

    def test_prunes_unattested_baal_verbal_when_nominal_variant_exists(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 1.5 I:10\t\t\t\t\t\t",
            "1\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg. cstr. gen.\tBaʿlu/Baal\t",
            "1\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb G act. ptcpl. m. sg. cstr. gen.\tto make\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["bˤl(II)/"],
        )

    def test_keeps_directly_attested_baal_verbal_variant(self) -> None:
        attestation_index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={("/b-ʕ-l/", ""): {normalize_reference_label("CAT 1.17 VI:24")}},
        )
        doc = self._doc_from_lines(
            "# KTU 1.17 VI:24\t\t\t\t\t\t",
            "1\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg. abs. nom.\tBaʿlu/Baal\t",
            "1\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb G act. ptcpl. m. sg. abs. nom.\tto make\t",
            attestation_index=attestation_index,
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["bˤl(II)/", "bˤl[/"],
        )

    def test_prunes_unattested_bt_house_variant_outside_baal_phrase(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 1.3 I:24\t\t\t\t\t\t",
            "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. cstr. gen.\thouse\t",
            "1\tbt\tb(t(I)/t\tbt (I)\tn. f. sg. cstr. gen.\tdaughter\t",
            "2\tar\tar/\tả/ỉr\tn. m. sg. abs. gen.\tlight\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["b(t(I)/t"],
        )

    def test_keeps_bt_house_variant_in_bt_l_baal_phrase(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 1.3 VI:3\t\t\t\t\t\t",
            "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. abs. nom.\thouse\t",
            "1\tbt\tb(t(I)/t\tbt (I)\tn. f. sg. abs. nom.\tdaughter\t",
            "2\tl\tl(I)\tl (I)\tprep.\tto\t",
            "3\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. pl. abs. gen.\tBaʿlu/Baal\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["bt(II)/"],
        )

    def test_keeps_directly_attested_bt_house_variant(self) -> None:
        attestation_index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={("bt", "II"): {normalize_reference_label("CAT 1.3 V:3")}},
        )
        doc = self._doc_from_lines(
            "# KTU 1.3 V:3\t\t\t\t\t\t",
            "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. abs. nom.\thouse\t",
            "1\tbt\tb(t(I)/t\tbt (I)\tn. f. sg. abs. nom.\tdaughter\t",
            attestation_index=attestation_index,
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["bt(II)/"],
        )

    def test_collapses_thr_il_sequence_to_bull_and_el(self) -> None:
        doc = self._doc_from_lines(
            "1\tṯr\tṯr(I)/\tṯr (I)\tn. m. pl. abs. nom.\tbull\t",
            "1\tṯr\tṯr(I)/\tṯr (I)\tn. m. sg. abs. nom.\tbull\t",
            "2\til\til(I)/\tỉl (I)\tDN sg. abs. nom.\tʾIlu/Ilu/El\t",
            "2\til\til(I)/\tỉl (I)\tDN sg. cstr. nom.\tʾIlu/Ilu/El\t",
            "2\til\til(I)/\tỉl (I)\tDN m. sg. abs. nom.\tʾIlu/Ilu/El\t",
            "2\til\til(I)/\tỉl (I)\tDN m. sg. cstr. nom.\tʾIlu/Ilu/El\t",
            "2\til\til(I)/\tỉl (I)\tn. m. sg. abs. nom.\tgod\t",
            "2\til\til(I)/\tỉl (I)\tn. m. sg. cstr. nom.\tgod\t",
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[0]._.resolved_candidates],
            ["ṯr(I)/"],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[0]._.resolved_candidates],
            ["n. m. sg. abs. nom."],
        )
        self.assertEqual(
            [candidate.analysis for candidate in doc[1]._.resolved_candidates],
            ["il(I)/"],
        )
        self.assertEqual(
            [candidate.pos for candidate in doc[1]._.resolved_candidates],
            ["DN m. sg. abs. nom."],
        )


class SpacyYdkContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_ydk_context_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.3.tsv"):
        tokens = parse_grouped_tokens(lines)
        doc = build_doc(self.nlp, tokens, source_name=source_name)
        return self.nlp(doc)

    def test_resolves_ydk_before_sgr(self) -> None:
        doc = self._doc_from_lines(
            "1	ydk	yd(I)/+k	yd (I)	n. f.	hand	",
            "1	ydk	yd(II)/+k	yd (II)	n. m.	love	",
            "2	ṣġr	ṣġr/	ṣġr	adj.	small	",
        )
        self.assertEqual(doc[0]._.resolved_candidates[0].analysis, "yd(II)/+k=")
        self.assertEqual(doc[0]._.resolved_candidates[0].pos, "n. m. cstr. nom.")


if __name__ == "__main__":
    unittest.main()
