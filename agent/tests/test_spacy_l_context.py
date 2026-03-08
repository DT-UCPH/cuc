import unittest

from spacy_ugaritic.doc_builder import build_doc, group_tablet_lines
from spacy_ugaritic.language import create_ugaritic_nlp


class SpacyLContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nlp = create_ugaritic_nlp()

    def _doc_from_lines(self, *lines: str, source_name: str = "KTU 1.3.tsv"):
        grouped = group_tablet_lines(lines)
        doc = build_doc(self.nlp, grouped, source_name=source_name)
        return self.nlp(doc)

    def test_groups_candidate_rows_into_one_token(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 1.3 IV:5\t\t\t\t\t\t",
            "1\tl\tl(I)\tl (I)\tprep.\tto\t",
            "1\tl\tl(II)\tl (II)\tadv.\tno\t",
            "2\tbt\tb(t(I)/t\tbt (I)\tn. f. sg.\tdaughter\t",
        )
        self.assertEqual(len(doc), 2)
        self.assertEqual(len(doc[0]._.candidates), 2)

    def test_ignores_empty_surface_rows(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 1.3 V:44\t\t\t\t\t\t",
            "1\tl\tl(I)\tl (I)\tprep.\tto\t",
            "2\t\t?\t?\t?\t?\t",
            "3\tkbd\tkbd(I)/\tkbd (I)\tn. m. sg.\tliver\t",
        )
        self.assertEqual([token.text for token in doc], ["l", "kbd"])

    def test_prefers_l_i_when_next_token_is_not_verbal(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 9.9 1\t\t\t\t\t\t",
            "1\tl\tl(I)\tl (I)\tprep.\tto\t",
            "1\tl\tl(II)\tl (II)\tadv.\tno\t",
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t",
            "2\tbt\tb(t(I)/t\tbt (I)\tn. f. sg.\tdaughter\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["l(I)"])

    def test_keeps_l_ii_when_next_token_is_verbal(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 9.9 1\t\t\t\t\t\t",
            "1\tl\tl(I)\tl (I)\tprep.\tto\t",
            "1\tl\tl(II)\tl (II)\tadv.\tno\t",
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t",
            "2\tyqm\t!y!qm[\t/q-w-m/\tvb G prefc.\tto rise\t",
        )
        self.assertIn("l(II)", [c.analysis for c in doc[0]._.resolved_candidates])

    def test_forces_l_iv_in_known_reference(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 1.24:15\t\t\t\t\t\t",
            "1\tl\tl(I)\tl (I)\tprep.\tto\t",
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t",
            "2\tkṯrt\tkṯrt/\tkṯrt\tDN\tKotharat\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["l(IV)"])

    def test_forces_l_i_for_kbd_compound(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 9.9 2\t\t\t\t\t\t",
            "1\tl\tl(I)\tl (I)\tprep.\tto\t",
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t",
            "2\tkbd\tkbd(I)/\tkbd (I)\tn. m. sg.\tliver\t",
            "2\tkbd\tkbd(II)/\tkbd (II)\tn. m. sg.\ttotal\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["l(I)"])
        self.assertEqual(doc[1]._.resolved_candidates[0].gloss, "within")

    def test_forces_l_i_for_high_confidence_bigram(self) -> None:
        doc = self._doc_from_lines(
            "# KTU 9.9 3\t\t\t\t\t\t",
            "1\tl\tl(I)\tl (I)\tprep.\tto\t",
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t",
            "2\tšpš\tšpš/\tšpš\tDN f.\tŠapšu/Shapsh/Shapshu\t",
        )
        self.assertEqual([c.analysis for c in doc[0]._.resolved_candidates], ["l(I)"])


if __name__ == "__main__":
    unittest.main()
