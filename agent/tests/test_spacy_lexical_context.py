"""Focused tests for the spaCy-based lexical context component."""

import unittest

from spacy_ugaritic.doc_builder import build_doc, parse_grouped_tokens
from spacy_ugaritic.language import (
    create_ugaritic_baal_context_nlp,
    create_ugaritic_ydk_context_nlp,
)


class SpacyBaalContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_baal_context_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.3.tsv"):
        tokens = parse_grouped_tokens(lines)
        doc = build_doc(self.nlp, tokens, source_name=source_name)
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
