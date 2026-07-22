"""Tests for strong-root G passive-participle suppression in form enrichment.

On a strong triradical root the G passive participle is spelled identically to
the finite forms and the noun; alphabetic writing cannot mark it (Notarius,
*The Ugaritic passive participle*, §2.2.1).  The parser therefore stops
enumerating it from the bare skeleton.  Weak-root, geminate, and explicitly
labelled participles are left untouched.
"""

import unittest
from pathlib import Path

from pipeline.steps.base import TabletRow
from pipeline.steps.verb_form_morph_pos import VerbFormMorphPosFixer


class _FormIndex:
    def __init__(self, mapping=None) -> None:
        self.mapping = dict(mapping or {})

    def morphologies_for(self, surface: str, dulat_token: str) -> set[str]:
        return set(self.mapping.get((surface, dulat_token), set()))


class PassiveParticipleSuppressionTest(unittest.TestCase):
    def _fixer(self, index):
        return VerbFormMorphPosFixer(dulat_db=Path("unused.sqlite"), form_index=index)

    def test_strong_root_passive_participle_is_dropped(self) -> None:
        index = _FormIndex({("rgm", "/r-g-m/"): {"G, suffc.", "G, pass., ptc., m., sg."}})
        row = TabletRow("1", "rgm", "rgm[", "/r-g-m/", "vb G", "to say", "")
        result = self._fixer(index).refine_row(row)
        self.assertIn("suffc.", result.pos)
        self.assertNotIn("pass. ptcpl.", result.pos)

    def test_iii_aleph_passive_participle_is_kept(self) -> None:
        index = _FormIndex({("nši", "/n-š-ʔ/"): {"G, pass., ptc., m., sg."}})
        row = TabletRow("2", "nši", "nš(ʔ[", "/n-š-ʔ/", "vb G", "to lift", "")
        result = self._fixer(index).refine_row(row)
        self.assertIn("pass. ptcpl.", result.pos)

    def test_geminate_passive_participle_is_kept(self) -> None:
        # DULAT writes the geminate root either fully or with a parenthesised
        # third radical; both stay untouched.
        for root in ("/b-r-r/", "/b-r(-r)/"):
            index = _FormIndex({("brr", root): {"G, pass., ptc., m., sg."}})
            row = TabletRow("3", "brr", "brr[", root, "vb G", "to purify", "")
            result = self._fixer(index).refine_row(row)
            self.assertIn("pass. ptcpl.", result.pos, root)

    def test_explicitly_labelled_passive_participle_is_kept(self) -> None:
        index = _FormIndex({("rgm", "/r-g-m/"): {"G, pass., ptc., m., sg."}})
        row = TabletRow("4", "rgm", "rgm[/", "/r-g-m/", "vb G pass. ptcpl.", "to say", "")
        result = self._fixer(index).refine_row(row)
        self.assertIn("pass. ptcpl.", result.pos)

    def test_active_participle_on_strong_root_is_kept(self) -> None:
        # Suppression is limited to the passive participle.
        index = _FormIndex({("rgm", "/r-g-m/"): {"G, act., ptc., m., sg."}})
        row = TabletRow("5", "rgm", "rgm[/", "/r-g-m/", "vb G", "to say", "")
        result = self._fixer(index).refine_row(row)
        self.assertIn("act. ptcpl.", result.pos)


if __name__ == "__main__":
    unittest.main()
