"""Tests for form-label extraction in DulatFeatureReader."""

import unittest
from pathlib import Path

from morph_features.dulat_feature_reader import DulatFeatureReader


class _Gate:
    def __init__(self, mapping: dict[tuple[str, str], set[str]]) -> None:
        self._mapping = mapping

    def surface_morphologies(self, dulat: str, surface: str) -> set[str]:
        return set(self._mapping.get((dulat, surface), set()))


class DulatFeatureReaderFormsTest(unittest.TestCase):
    def test_with_suff_does_not_add_suffix_conjugation(self) -> None:
        reader = DulatFeatureReader(
            db_path=Path("missing.sqlite"),
            gate=_Gate({("/n-ʔ-ṣ/", "ynaṣn"): {"G, prefc., with suff."}}),
        )
        features = reader.read_surface_features("ynaṣn", "/n-ʔ-ṣ/")
        self.assertEqual(features.forms, ("prefc.",))

    def test_bare_suff_maps_to_suffix_conjugation(self) -> None:
        reader = DulatFeatureReader(
            db_path=Path("missing.sqlite"),
            gate=_Gate({("/q-b/", "yqbh"): {"G, suff."}}),
        )
        features = reader.read_surface_features("yqbh", "/q-b/")
        self.assertEqual(features.forms, ("suffc.",))


if __name__ == "__main__":
    unittest.main()
