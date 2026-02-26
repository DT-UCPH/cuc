"""Tests for deictic functor extended -m enclitic encoding."""

import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.deictic_functor_enclitic_m import DeicticFunctorEncliticMFixer


class _FormGate:
    def __init__(self, forms=None) -> None:
        self.forms = dict(forms or {})

    def has_surface_form(self, token: str, surface: str) -> bool:
        return bool(self.forms.get((token, surface), False))


class DeicticFunctorEncliticMFixerTest(unittest.TestCase):
    def test_rewrites_hl_extended_form_to_enclitic_m(self) -> None:
        gate = _FormGate({("hl", "hlm"): True})
        fixer = DeicticFunctorEncliticMFixer(gate=gate)
        row = TabletRow("1", "hlm", "hl", "hl", "deictic adv. functor", "behold", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hl~m")

    def test_keeps_non_functor_unchanged(self) -> None:
        gate = _FormGate({("hl", "hlm"): True})
        fixer = DeicticFunctorEncliticMFixer(gate=gate)
        row = TabletRow("2", "hlm", "hl", "hl", "n. m.", "something", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hl")


if __name__ == "__main__":
    unittest.main()
