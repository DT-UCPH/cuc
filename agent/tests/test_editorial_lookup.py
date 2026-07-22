"""Tests for safe lexical lookup aliases from KTU editorial notation."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import extract_lexeme_from_analysis, ktu_corrected_surface_from_annotation
from pipeline.steps.analysis_utils import analysis_matches_surface
from scripts.refine_results_mentions import Entry, refine_file
from text_fabric.editorial_lookup import (
    corrected_editorial_lookup_surface,
    load_editorial_lookup_overrides,
)


class EditorialLookupTest(unittest.TestCase):
    def test_linter_recovers_corrected_lookup_surface_from_comment(self) -> None:
        self.assertEqual(
            ktu_corrected_surface_from_annotation(
                "Migrated | KTU corrected: gpn | DULAT direct ref"
            ),
            "gpn",
        )
        self.assertIsNone(ktu_corrected_surface_from_annotation("DULAT direct ref"))

    def test_excised_sign_is_removed_from_corrected_lookup(self) -> None:
        self.assertEqual(corrected_editorial_lookup_surface("gmpn", "g[[m]]pn"), "gpn")

    def test_redundant_sign_is_removed_with_allograph_normalization(self) -> None:
        self.assertEqual(corrected_editorial_lookup_surface("ṣpˤn", "ṣp{ʿ}n"), "ṣpn")

    def test_missing_and_restored_signs_remain_in_normalized_reading(self) -> None:
        self.assertIsNone(corrected_editorial_lookup_surface("nḫtu", "<n>ḫtu"))
        self.assertIsNone(corrected_editorial_lookup_surface("bnh", "[b]nh"))

    def test_missing_and_restored_content_survives_an_actual_correction(self) -> None:
        self.assertEqual(corrected_editorial_lookup_surface("abcd", "a{b}<c>d"), "acd")
        self.assertEqual(corrected_editorial_lookup_surface("abcd", "a{b}[c]d"), "acd")

    def test_other_editorial_separators_do_not_create_lexical_aliases(self) -> None:
        self.assertIsNone(corrected_editorial_lookup_surface("bn", "b+n"))
        self.assertIsNone(corrected_editorial_lookup_surface("bn", "b(+)n"))
        self.assertIsNone(corrected_editorial_lookup_surface("bn", "b.n"))
        self.assertIsNone(corrected_editorial_lookup_surface("bn", "b\\n"))

    def test_unsafe_or_unhelpful_aliases_are_rejected(self) -> None:
        self.assertIsNone(corrected_editorial_lookup_surface("x", "[[x]]"))
        self.assertIsNone(
            corrected_editorial_lookup_surface("lwkmwkm", "l[[w]]km .[[w]]km")
        )
        self.assertIsNone(corrected_editorial_lookup_surface("gmpn", "x[[m]]pn"))

    def test_loads_alias_by_token_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = Path(tmp_dir) / "KTU 1.5.tsv"
            source.write_text("158634\tgmpn\tgmpn\tg[[m]]pn\n", encoding="utf-8")
            self.assertEqual(load_editorial_lookup_overrides(source), {"158634": "gpn"})

    def test_refinement_uses_corrected_lookup_but_renders_physical_surface(self) -> None:
        entry = Entry(
            entry_id=1592,
            lemma="gpn",
            hom="III",
            pos="DN m.",
            gloss="Gapnu",
            wiki_tr="",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "KTU 1.5.tsv"
            output.write_text(
                "#---------------------------- KTU 1.5 I:12\n"
                "158634\tgmpn\t?\t?\t?\t?\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )
            rows, changed = refine_file(
                path=output,
                out_path=output,
                forms_map={"gpn": [entry]},
                lemma_map={"gpn": [entry]},
                suffix_map={},
                forms_morph={},
                reverse_mentions={},
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                editorial_lookup_overrides={"158634": "gpn"},
            )
            self.assertEqual((rows, changed), (1, 1))
            row = output.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn(
                "\tg&mpn(III)/\tgpn (III)\tDN m.\tGapnu\tKTU corrected: gpn",
                row,
            )
            self.assertTrue(analysis_matches_surface("gmpn", "g&mpn(III)/"))

    def test_editorial_lookup_preserves_exact_lemma_homonyms_missing_from_forms(self) -> None:
        common = Entry(1590, "gpn", "I", "n. m.", "vine", "")
        divine = Entry(1592, "gpn", "III", "DN m.", "Gapnu", "")
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "KTU 1.5.tsv"
            output.write_text(
                "#---------------------------- KTU 1.5 I:12\n"
                "158634\tgmpn\t?\t?\t?\t?\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )
            refine_file(
                path=output,
                out_path=output,
                forms_map={"gpn": [common]},
                lemma_map={"gpn": [common, divine]},
                suffix_map={},
                forms_morph={("gpn", 1590): {"sg."}},
                reverse_mentions={"CAT 1.5 I:12": {1592}},
                entry_ref_count={1590: 3, 1592: 4},
                entry_tablets={1590: {"1.23"}, 1592: {"1.5"}},
                entry_family_count={1590: {"1": 1}, 1592: {"1": 4}},
                editorial_lookup_overrides={"158634": "gpn"},
            )
            row = output.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("g&mpn(III)/", row)
            self.assertIn("gpn (III)", row)

    def test_trailing_excised_sign_keeps_homonym_on_lexical_host(self) -> None:
        entry = Entry(1, "spr", "II", "n. m.", "tablet", "")
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "KTU 3.10.tsv"
            output.write_text(
                "181006\tspxrn\t?\t?\t?\t?\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )
            refine_file(
                path=output,
                out_path=output,
                forms_map={"sprn": [entry]},
                lemma_map={"spr": [entry]},
                suffix_map={},
                forms_morph={},
                reverse_mentions={},
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                editorial_lookup_overrides={"181006": "sprn"},
            )
            self.assertIn("\tsp&xr(II)&n/\t", output.read_text(encoding="utf-8"))
            self.assertEqual(
                extract_lexeme_from_analysis("sp&xr(II)&n/"),
                ("spr", False, "II"),
            )


if __name__ == "__main__":
    unittest.main()
