"""Focused tests for the spaCy-based formula context component."""

import unittest

from spacy_ugaritic.language import create_ugaritic_formula_context_nlp
from spacy_ugaritic.row_builder import build_row_doc, parse_rows


class SpacyFormulaContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_formula_context_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.3.tsv"):
        rows = parse_rows(lines)
        doc = build_row_doc(self.nlp, rows, source_name=source_name)
        return self.nlp(doc)

    def test_rewrites_bigram_target(self) -> None:
        doc = self._doc_from_lines(
            "1\taliyn\taliyn/\tảlỉyn\tadj. m.\tThe Very / Most Powerful\t",
            "2\tbˤl\tbˤl(II)/;bˤl[\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\t",
        )
        self.assertEqual(doc[1]._.resolved_row.analysis, "bˤl(II)/")
        self.assertEqual(doc[1]._.resolved_row.pos, "DN")

    def test_rewrites_trigram_target_only_when_variants_exist(self) -> None:
        doc = self._doc_from_lines(
            (
                "1\trbt\trbt/;rbt(I)/;rbt(II)/\trb(b)t;rbt (I);rbt (II)\t"
                "num.;n. f.;n. f.\tten thousand;Lady;seine\t"
            ),
            "2\taṯrt\taṯrt(II)/\tảṯrt (II)\tDN\tAsherah\t",
            "3\tym\tym(II)/\tym (II)\tn. m.\tsea\t",
        )
        self.assertEqual(doc[0]._.resolved_row.analysis, "rbt(I)/")
        self.assertEqual(doc[0]._.resolved_row.gloss, "Lady")

    def test_skips_trigram_rewrite_for_single_variant_style(self) -> None:
        doc = self._doc_from_lines(
            "1\trbt\trb(t(I)/t\trbt (I)\tn. f.\tLady\t",
            "2\taṯrt\taṯrt(II)/\tảṯrt (II)\tDN\tAsherah\t",
            "3\tym\tym(II)/\tym (II)\tn. m.\tsea\t",
        )
        self.assertEqual(doc[0]._.resolved_row.analysis, "rb(t(I)/t")


if __name__ == "__main__":
    unittest.main()
