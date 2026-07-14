"""Tests for deictic functor extended -m enclitic encoding."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

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

    def test_uses_note_listed_extended_form_when_exact_form_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE entries("
                "entry_id INTEGER PRIMARY KEY, lemma TEXT, homonym TEXT, pos TEXT)"
            )
            cur.execute(
                "CREATE TABLE forms("
                "entry_id INTEGER, text TEXT, morphology TEXT, cert TEXT, notes TEXT)"
            )
            cur.execute(
                "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (1, 'hl', '', '')"
            )
            cur.execute(
                "INSERT INTO forms(entry_id, text, morphology, cert, notes) "
                "VALUES (1, 'hl', '', '', 'suff. / ext. forms: <i>hlk</i>, <i>hlh</i>, <i>hlm</i>')"
            )
            conn.commit()
            conn.close()

            fixer = DeicticFunctorEncliticMFixer(dulat_db=db_path)
            row = TabletRow("3", "hlm", "hl", "hl", "deictic adv. functor", "behold", "")
            result = fixer.refine_row(row)
            self.assertEqual(result.analysis, "hl~m")


if __name__ == "__main__":
    unittest.main()
