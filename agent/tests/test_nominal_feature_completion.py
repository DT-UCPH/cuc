"""Tests for deterministic nominal completion."""

import unittest
from pathlib import Path

from morph_features.dulat_feature_reader import DulatFeatureReader
from morph_features.nominal_completion import NominalFeatureCompleter, rewrite_row
from pipeline.steps.base import TabletRow


class _FakeReader(DulatFeatureReader):
    def __init__(self, mapping=None):
        self.mapping = dict(mapping or {})
        super().__init__(db_path=Path("unused.sqlite"))

    def read_surface_features(self, surface: str, dulat: str, pos: str = ""):
        if (surface, dulat) in self.mapping:
            return self.mapping[(surface, dulat)]
        return super().read_surface_features(surface, dulat, pos)


class _Features:
    def __init__(self, morphologies):
        self.morphologies = tuple(morphologies)
        self.forms = tuple()
        self.genders = tuple()
        self.numbers = tuple()
        self.states = tuple()
        self.cases = tuple()


class NominalFeatureCompletionTest(unittest.TestCase):
    def test_splits_exact_surface_nominal_number_and_state(self) -> None:
        completer = NominalFeatureCompleter(
            _FakeReader({("bn", "bn (I)"): _Features(("sg.", "pl., cstr."))})
        )
        row = TabletRow("139796", "bn", "bn(I)/", "bn (I)", "n. m.", "son", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(
            rewritten.pos,
            "n. m. sg. abs. nom.; n. m. pl. cstr. nom.",
        )

    def test_marks_suffix_bearing_nominal_as_construct(self) -> None:
        completer = NominalFeatureCompleter(_FakeReader({("ipdk", "ỉpd"): _Features(("suff.",))}))
        row = TabletRow("139786", "ipdk", "ipd/+k", "ỉpd", "n. m.", "tunic", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "n. m. cstr. nom.")

    def test_keeps_feminine_singular_when_surface_and_dulat_agree(self) -> None:
        completer = NominalFeatureCompleter(_FakeReader({("brlt", "brlt"): _Features(("sg.",))}))
        row = TabletRow("139839", "brlt", "brl(t/t", "brlt", "n. f.", "hunger", "")
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "n. f. sg. abs. nom.")

    def test_preserves_name_class_while_defaulting_to_singular(self) -> None:
        completer = NominalFeatureCompleter(_FakeReader({("ṣpn", "ṣpn"): _Features(("",))}))
        row = TabletRow(
            "139817",
            "ṣpn",
            "ṣpn/",
            "ṣpn",
            "TN/DN",
            "Ṣapānu/Zaphon/the mountain dwelling of bʕl deified",
            "",
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "TN/DN sg. abs. nom.")

    def test_defaults_names_to_singular_when_no_number_is_available(self) -> None:
        completer = NominalFeatureCompleter(_FakeReader({("ṣpn", "ṣpn"): _Features(("",))}))
        row = TabletRow(
            "139817",
            "ṣpn",
            "ṣpn/",
            "ṣpn",
            "TN/DN",
            "Ṣapānu/Zaphon/the mountain dwelling of bʕl deified",
            "",
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "TN/DN sg. abs. nom.")

    def test_defaults_adjectives_to_absolute_nominative(self) -> None:
        completer = NominalFeatureCompleter(_FakeReader({("aliyn", "ảlỉyn"): _Features(("sg.",))}))
        row = TabletRow(
            "135903", "aliyn", "aliyn/", "ảlỉyn", "adj. m. sg.", "The Very / Most Powerful", ""
        )
        rewritten = rewrite_row(row, completer)
        self.assertEqual(rewritten.pos, "adj. m. sg. abs. nom.")


if __name__ == "__main__":
    unittest.main()
