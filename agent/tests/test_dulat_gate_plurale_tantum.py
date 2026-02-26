"""Tests for DULAT plurale-tantum gate classification."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.steps.dulat_gate import DulatMorphGate


class DulatGatePluraleTantumTest(unittest.TestCase):
    def _build_gate(self) -> DulatMorphGate:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE entries (
                    entry_id INTEGER PRIMARY KEY,
                    lemma TEXT,
                    homonym TEXT,
                    pos TEXT,
                    gender TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE forms (
                    entry_id INTEGER,
                    text TEXT,
                    morphology TEXT
                )
                """
            )

            cur.executemany(
                "INSERT INTO entries(entry_id, lemma, homonym, pos, gender) VALUES (?, ?, ?, ?, ?)",
                [
                    (1, "pnm", "", "n.", "m."),
                    (2, "šlm", "II", "n.", "m."),
                    (3, "qm", "", "n.", "m."),
                    (4, "ḥlm", "II", "n.", "m."),
                    (5, "ʕgm", "", "n.", "m."),
                    (6, "ỉštnm", "", "n.", "m."),
                    (7, "ủm", "", "n.", "f."),
                    (8, "ỉl", "I", "n.", "m."),
                    (9, "tḥm", "", "n.", "m."),
                    (10, "s:śs/św", "", "n.", "m."),
                ],
            )
            cur.executemany(
                "INSERT INTO forms(entry_id, text, morphology) VALUES (?, ?, ?)",
                [
                    (1, "pn", "pl., cstr."),
                    (1, "pnm", "pl."),
                    (1, "pnh", "suff."),
                    (2, "šlmm", "pl."),
                    (2, "šlmm", "sg., suff."),
                    (2, "-m", "sg., suff."),
                    (3, "qm", "pl., cstr."),
                    (4, "ḥlmm", "pl."),
                    (5, "ʕgmm", "pl."),
                    (6, "ỉštnm", "pl."),
                    (7, "ủmy", "sg."),
                    (7, "ủmy", "suff."),
                    (7, "ủmm", "du."),
                    (8, "ỉl", "sg."),
                    (8, "ỉl", "du., cstr."),
                    (8, "ỉly", "du., cstr."),
                    (9, "tḥmk", "sg."),
                    (10, "śśwm", "pl."),
                ],
            )
            conn.commit()
            conn.close()

            gate = DulatMorphGate(db_path)
        return gate

    def test_ignores_explicit_singular_suffix_evidence_for_plurale_tantum(self) -> None:
        gate = self._build_gate()
        self.assertTrue(gate.is_plurale_tantum_noun_token("pnm"))
        self.assertFalse(gate.is_plurale_tantum_noun_token("šlm (II)"))
        self.assertFalse(gate.is_plurale_tantum_noun_token("qm"))
        self.assertFalse(gate.is_plurale_tantum_noun_token("ḥlm (II)"))
        self.assertFalse(gate.is_plurale_tantum_noun_token("ʕgm"))
        self.assertFalse(gate.is_plurale_tantum_noun_token("ištnm"))

    def test_returns_surface_morphologies_for_exact_form(self) -> None:
        gate = self._build_gate()
        self.assertEqual(gate.surface_morphologies("ủm", "umy"), {"sg.", "suff."})

    def test_returns_empty_surface_morphologies_for_missing_form(self) -> None:
        gate = self._build_gate()
        self.assertEqual(gate.surface_morphologies("ủm", "umh"), set())

    def test_treats_dual_surface_form_as_plural_for_split_gate(self) -> None:
        gate = self._build_gate()
        self.assertTrue(gate.is_plural_token("ủm", surface="ủmm"))

    def test_exposes_token_genders(self) -> None:
        gate = self._build_gate()
        self.assertEqual(gate.token_genders("ủm"), {"f."})
        self.assertEqual(gate.token_genders("pnm"), {"m."})

    def test_applies_il_construct_form_morphology_overrides(self) -> None:
        gate = self._build_gate()
        self.assertEqual(gate.surface_morphologies("ỉl (I)", "il"), {"sg.", "sg., cstr."})
        self.assertEqual(gate.surface_morphologies("ỉl (I)", "ily"), {"pl., cstr."})

    def test_applies_thm_tahmak_suffix_morphology_override(self) -> None:
        gate = self._build_gate()
        self.assertTrue(gate.has_suffix_token("tḥm", surface="tḥmk"))

    def test_preserves_non_ascii_form_letters_for_surface_matching(self) -> None:
        gate = self._build_gate()
        self.assertTrue(gate.has_surface_form("s:śs/św", "śśwm"))
        self.assertEqual(gate.surface_morphologies("s:śs/św", "śśwm"), {"pl."})
        self.assertFalse(gate.has_surface_form("s:śs/św", "wm"))


if __name__ == "__main__":
    unittest.main()
