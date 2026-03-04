"""Focused tests for the spaCy-based formula context component."""

import unittest

from spacy_ugaritic.doc_builder import build_doc, parse_row_tokens
from spacy_ugaritic.language import create_ugaritic_formula_context_nlp


class SpacyFormulaContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_formula_context_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.3.tsv"):
        tokens = parse_row_tokens(lines)
        doc = build_doc(self.nlp, tokens, source_name=source_name)
        return self.nlp(doc)

    def test_rewrites_bigram_target(self) -> None:
        doc = self._doc_from_lines(
            "1	aliyn	aliyn/	ảlỉyn	adj. m.	The Very / Most Powerful	",
            "2	bˤl	bˤl(II)/;bˤl[	bʕl (II);/b-ʕ-l/	n. m./DN;vb	Baʿlu;to make	",
        )
        self.assertEqual(doc[1]._.resolved_candidates[0].analysis, "bˤl(II)/")
        self.assertEqual(doc[1]._.resolved_candidates[0].pos, "DN")

    def test_rewrites_trigram_target_only_when_variants_exist(self) -> None:
        doc = self._doc_from_lines(
            (
                "1	rbt	rbt/;rbt(I)/;rbt(II)/	rb(b)t;rbt (I);rbt (II)	"
                "num.;n. f.;n. f.	ten thousand;Lady;seine	"
            ),
            "2	aṯrt	aṯrt(II)/	ảṯrt (II)	DN	Asherah	",
            "3	ym	ym(II)/	ym (II)	n. m.	sea	",
        )
        self.assertEqual(doc[0]._.resolved_candidates[0].analysis, "rbt(I)/")
        self.assertEqual(doc[0]._.resolved_candidates[0].gloss, "Lady")

    def test_skips_trigram_rewrite_for_single_variant_style(self) -> None:
        doc = self._doc_from_lines(
            "1	rbt	rb(t(I)/t	rbt (I)	n. f.	Lady	",
            "2	aṯrt	aṯrt(II)/	ảṯrt (II)	DN	Asherah	",
            "3	ym	ym(II)/	ym (II)	n. m.	sea	",
        )
        self.assertEqual(doc[0]._.resolved_candidates[0].analysis, "rb(t(I)/t")


if __name__ == "__main__":
    unittest.main()
