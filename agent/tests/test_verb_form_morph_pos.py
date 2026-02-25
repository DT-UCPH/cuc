"""Tests for DULAT form-aware verb POS enrichment."""

import unittest
from pathlib import Path

from pipeline.steps.base import TabletRow
from pipeline.steps.verb_form_morph_pos import VerbFormMorphPosFixer


class _FormIndex:
    def __init__(self, mapping=None) -> None:
        self.mapping = dict(mapping or {})

    def morphologies_for(self, surface: str, dulat_token: str) -> set[str]:
        return set(self.mapping.get((surface, dulat_token), set()))


class VerbFormMorphPosFixerTest(unittest.TestCase):
    def test_appends_prefc_label(self) -> None:
        index = _FormIndex({("ytn", "/y-t-n/"): {"G, prefc."}})
        fixer = VerbFormMorphPosFixer(dulat_db=Path("unused.sqlite"), form_index=index)
        row = TabletRow("1", "ytn", "!y!ytn[", "/y-t-n/", "vb G", "to give", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "vb G prefc.")

    def test_expands_ambiguous_form_options(self) -> None:
        index = _FormIndex(
            {
                ("qtl", "/q-t-l/"): {
                    "G, prefc.",
                    "G, impv.",
                    "G, pass., ptc., m., sg.",
                }
            }
        )
        fixer = VerbFormMorphPosFixer(dulat_db=Path("unused.sqlite"), form_index=index)
        row = TabletRow("2", "qtl", "qtl[", "/q-t-l/", "vb G", "to kill", "")
        result = fixer.refine_row(row)
        self.assertEqual(
            result.pos,
            "vb G prefc. / vb G impv. / vb G pass. ptcpl. m. sg.",
        )

    def test_uses_existing_stem_when_multiple_stems_present(self) -> None:
        index = _FormIndex({("tṯbr", "/ṯ-b-r/"): {"G, prefc.", "N, prefc."}})
        fixer = VerbFormMorphPosFixer(dulat_db=Path("unused.sqlite"), form_index=index)
        row = TabletRow("3", "tṯbr", "!t!](n]ṯbr[", "/ṯ-b-r/", "vb N", "to break", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "vb N prefc.")

    def test_non_verbal_pos_unchanged(self) -> None:
        index = _FormIndex({("mlk", "mlk"): {"sg."}})
        fixer = VerbFormMorphPosFixer(dulat_db=Path("unused.sqlite"), form_index=index)
        row = TabletRow("4", "mlk", "mlk/", "mlk", "n. m.", "king", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "n. m.")

    def test_semicolon_variants_are_rewritten_per_variant(self) -> None:
        index = _FormIndex(
            {
                ("qtl", "/q-t-l/"): {"G, prefc."},
            }
        )
        fixer = VerbFormMorphPosFixer(dulat_db=Path("unused.sqlite"), form_index=index)
        row = TabletRow(
            "5",
            "qtl",
            "qtl[;qtl/",
            "/q-t-l/;qtl",
            "vb G;n. m.",
            "to kill;killer",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "vb G prefc.; n. m.")

    def test_uses_analysis_host_when_surface_includes_suffix_payload(self) -> None:
        index = _FormIndex({("yšqy", "/š-q-y/"): {"G, prefc."}})
        fixer = VerbFormMorphPosFixer(dulat_db=Path("unused.sqlite"), form_index=index)
        row = TabletRow(
            "6",
            "yšqynh",
            "!y!šqy[+nh",
            "/š-q-y/",
            "vb",
            "to offer (something to) drink",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.pos, "vb G prefc.")


if __name__ == "__main__":
    unittest.main()
