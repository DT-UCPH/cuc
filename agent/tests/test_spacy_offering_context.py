"""Focused tests for the spaCy-based offering context component."""

import unittest

from spacy_ugaritic.language import create_ugaritic_offering_context_nlp
from spacy_ugaritic.row_builder import build_row_doc, parse_rows


class SpacyOfferingContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_offering_context_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.119.tsv"):
        rows = parse_rows(lines)
        doc = build_row_doc(self.nlp, rows, source_name=source_name)
        return self.nlp(doc)

    def test_rewrites_ambiguous_l_in_offering_sequence(self) -> None:
        doc = self._doc_from_lines(
            "154176	gdlt	gdl(I)/t=	gdlt (I)	n. f.	head of cattle	",
            (
                "154177	l	l(I);l(II);l(III)	l (I);l (II);l (III)"
                "	prep.;adv.;functor	to;no;certainly	"
            ),
            "154178	bˤlm	bˤl(II)/m	bʕl (II)	n. m.	lord	",
        )
        self.assertEqual(doc[1]._.resolved_row.analysis, "l(I)")
        self.assertEqual(doc[1]._.resolved_row.pos, "prep.")
        self.assertEqual(doc[1]._.resolved_row.gloss, "to")

    def test_skips_non_offering_context(self) -> None:
        doc = self._doc_from_lines(
            "135588	ḥẓr	ḥẓr/	ḥẓr	n. m.	mansion	",
            (
                "135589	l	l(I);l(II);l(III)	l (I);l (II);l (III)"
                "	prep.;adv.;functor	to;no;certainly	"
            ),
            "135590	pˤn	pˤn/	pʕn	n. f.	foot	",
            source_name="KTU 1.1.tsv",
        )
        self.assertEqual(doc[1]._.resolved_row.analysis, "l(I);l(II);l(III)")


if __name__ == "__main__":
    unittest.main()
