"""Tests for form-aware nominal POS refinements (gender/dual)."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.nominal_form_morph_pos import NominalFormMorphPosFixer


class _MorphGate:
    def __init__(self, mapping=None, token_genders=None) -> None:
        self.mapping = dict(mapping or {})
        self.genders = dict(token_genders or {})

    def surface_morphologies(self, token: str, surface: str) -> set[str]:
        return set(self.mapping.get((token, surface), set()))

    def token_genders(self, token: str) -> set[str]:
        return set(self.genders.get(token, set()))


class NominalFormMorphPosFixerTest(unittest.TestCase):
    def test_promotes_masculine_pos_to_feminine_for_feminine_surface_form(self) -> None:
        gate = _MorphGate({("pḥl", "pḥlt"): {"f."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("1", "pḥlt", "pḥl/t", "pḥl", "n. m.", "ass", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. f. sg.")

    def test_appends_dual_marker_when_surface_form_is_dual(self) -> None:
        gate = _MorphGate({("š", "šm"): {"du."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("2", "šm", "š/m", "š", "n. m.", "ram", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. du.")

    def test_does_not_append_dual_when_same_surface_is_singular_and_dual(self) -> None:
        gate = _MorphGate({("ỉl (I)", "il"): {"sg.", "du., cstr."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("2b", "il", "il(I)/", "ỉl (I)", "n. m.", "god", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. sg. / n. m. du.")

    def test_removes_existing_dual_when_same_surface_is_singular_and_dual(self) -> None:
        gate = _MorphGate({("ỉl (I)", "il"): {"sg.", "du., cstr."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("2c", "il", "il(I)/", "ỉl (I)", "n. m. du.", "god", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. sg. / n. m. du.")

    def test_removes_existing_dual_when_surface_is_plural_construct(self) -> None:
        gate = _MorphGate({("ỉl (I)", "ily"): {"pl., cstr."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("2d", "ily", "il(I)/y", "ỉl (I)", "n. m. du.", "god", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m.")

    def test_emits_ambiguous_plural_or_dual_options(self) -> None:
        gate = _MorphGate({("pnm", "pn"): {"pl.", "du."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("2e", "pn", "pn(m/m", "pnm", "n. m.", "face", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. pl. / n. m. du.")

    def test_adds_construct_marker_for_construct_plural_ambiguity(self) -> None:
        gate = _MorphGate({("zbl (I)", "zbl"): {"sg.", "pl., cst."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("2e2", "zbl", "zbl(I)/", "zbl (I)", "n. m.", "prince", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. sg. / n. m. pl. cstr.")

    def test_dedupes_preexisting_ambiguous_number_options(self) -> None:
        gate = _MorphGate({("ỉšd", "išdk"): {"pl.", "du., suff."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow(
            "2f",
            "išdk",
            "išd/+k",
            "ỉšd",
            "n. m. pl. / n. m. pl. / n. m. pl. / n. m. du.",
            "leg",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. pl. cstr. / n. m. du. cstr.")

    def test_non_nominal_pos_unchanged(self) -> None:
        gate = _MorphGate({("hl", "hlm"): {"sg."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("3", "hlm", "hl~m", "hl", "deictic adv. functor", "behold", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "deictic adv. functor")

    def test_does_not_treat_suff_as_feminine_marker(self) -> None:
        gate = _MorphGate({("ảb", "abn"): {"sg., suff."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("4", "abn", "ab/+n", "ảb", "n. m.", "father", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. cstr.")

    def test_demotes_false_feminine_pos_when_token_gender_is_masculine(self) -> None:
        gate = _MorphGate(
            mapping={("ảb", "abn"): {"sg., suff."}},
            token_genders={"ảb": {"m."}},
        )
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("5", "abn", "ab/+n", "ảb", "n. f.", "father", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m. cstr.")

    def test_marks_adjective_with_pronominal_suffix_as_construct(self) -> None:
        gate = _MorphGate({("mrủ (I)", "mruh"): {"m., sg., suff."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("5b", "mruh", "mru(I)/+h", "mrủ (I)", "adj. m. sg.", "fattened", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "adj. m. sg. cstr.")

    def test_adds_singular_marker_for_feminine_t_split(self) -> None:
        fixer = NominalFormMorphPosFixer(gate=_MorphGate())
        row = TabletRow("6", "ṣrrt", "ṣrr(t/t", "ṣrrt", "n. f.", "appearance", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. f. sg.")

    def test_adds_plural_marker_for_feminine_t_equal_split(self) -> None:
        fixer = NominalFormMorphPosFixer(gate=_MorphGate())
        row = TabletRow("7", "ṣrrt", "ṣrr(t/t=", "ṣrrt", "n. f.", "appearance", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. f. pl.")

    def test_keeps_existing_number_marker_for_feminine_split_rows(self) -> None:
        fixer = NominalFormMorphPosFixer(gate=_MorphGate())
        row = TabletRow("8", "ṯknt", "ṯkn(t/t=", "ṯknt", "n. f. pl.", "appearance", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. f. pl.")

    def test_overrides_conflicting_plural_marker_for_feminine_singular_split(self) -> None:
        fixer = NominalFormMorphPosFixer(gate=_MorphGate())
        row = TabletRow("8b", "ġrt", "ġr(t(I)/t", "ġrt (I)", "n. f. pl.", "rock", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. f. sg.")

    def test_overrides_conflicting_singular_marker_for_feminine_plural_split(self) -> None:
        fixer = NominalFormMorphPosFixer(gate=_MorphGate())
        row = TabletRow("8c", "ġrt", "ġr(t(I)/t=", "ġrt (I)", "n. f. sg.", "rock", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. f. pl.")

    def test_adds_number_marker_for_feminine_split_numeral_rows(self) -> None:
        fixer = NominalFormMorphPosFixer(gate=_MorphGate())
        singular_row = TabletRow("9", "rbt", "rb(t/t", "rb(b)t", "num.", "ten thousand", "")
        singular_result = fixer.refine_row(singular_row)
        self.assertEqual(singular_result.pos, "num. sg.")

        plural_row = TabletRow("10", "rbt", "rb(t/t=", "rb(b)t", "num.", "ten thousand", "")
        plural_result = fixer.refine_row(plural_row)
        self.assertEqual(plural_result.pos, "num. pl.")

    def test_keeps_num_head_when_feminine_marker_is_present(self) -> None:
        gate = _MorphGate({("ṯn (I)", "ṯt"): {"f.", "sg."}})
        fixer = NominalFormMorphPosFixer(gate=gate)
        row = TabletRow("11", "ṯt", "ṯn(I)/", "ṯn (I)", "num.", "two", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "num. f.")


if __name__ == "__main__":
    unittest.main()
