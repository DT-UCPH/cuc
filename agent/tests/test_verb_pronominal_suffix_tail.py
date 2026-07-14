"""Tests for verbal raw suffix-tail normalization."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.verb_pronominal_suffix_tail import VerbPronominalSuffixTailFixer


class _FormIndex:
    def __init__(self, mapping: dict[tuple[str, str], set[str]]) -> None:
        self._mapping = mapping

    def morphologies_for(self, surface: str, dulat_token: str) -> set[str]:
        return set(self._mapping.get((surface, dulat_token), set()))


class VerbPronominalSuffixTailFixerTest(unittest.TestCase):
    def test_normalizes_l_stem_prefixed_form_with_suffix_pronoun(self) -> None:
        fixer = VerbPronominalSuffixTailFixer(
            dulat_db=None,
            form_index=_FormIndex({("yknnh", "/k-n/"): {"L, prefc., suff."}}),
        )
        row = TabletRow(
            "1",
            "yknnh",
            "!y!knn[h:l",
            "/k-n/",
            "vb L prefc. 3 m. sg.",
            "to establish, interpose, bring up",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!knn[:l+h")

    def test_normalizes_prefixed_d_stem_suffix_after_marker(self) -> None:
        fixer = VerbPronominalSuffixTailFixer(
            dulat_db=None,
            form_index=_FormIndex({("tšlmk", "/š-l-m/"): {"D, prefc., suff."}}),
        )
        row = TabletRow(
            "2",
            "tšlmk",
            "!t!šlm[k:d",
            "/š-l-m/",
            "vb D prefc.",
            "to be well",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!šlm[:d+k")

    def test_keeps_suffix_conjugation_ending_unchanged(self) -> None:
        fixer = VerbPronominalSuffixTailFixer(
            dulat_db=None,
            form_index=_FormIndex({("qlt", "/q-l/"): {"G, suffc."}}),
        )
        row = TabletRow(
            "3",
            "qlt",
            "ql[t",
            "/q-l/",
            "vb G suffc. 1 c. sg.",
            "to fall (down)",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ql[t")

    def test_keeps_prefixed_plural_ending_without_suffix_note_unchanged(self) -> None:
        fixer = VerbPronominalSuffixTailFixer(
            dulat_db=None,
            form_index=_FormIndex({("tdbḥn", "/d-b-ḥ/"): {"G, prefc., 2 f. pl."}}),
        )
        row = TabletRow(
            "4",
            "tdbḥn",
            "!t!dbḥ[n",
            "/d-b-ḥ/",
            "vb G prefc.",
            "to sacrifice",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!dbḥ[n")


if __name__ == "__main__":
    unittest.main()
