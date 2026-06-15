"""Regression tests for onomastic POS allowlist expansion in linter."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterOnomasticPosAllowlistTest(unittest.TestCase):
    def test_dn_pos_allowed_when_onomastic_override_declares_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "auto_parsing" / "0.2.6"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\til\til(I)/\tỉl (I)\tDN m. sg. cstr. gen.\tEl\t\n"
                ),
                encoding="utf-8",
            )

            entry = DulatEntry(
                entry_id=1,
                lemma="ỉl",
                homonym="I",
                pos="n.",
                gloss="god",
                morph="n. m.",
                form_text="il",
            )
            issues = lint_file(
                path=path,
                dulat_forms={normalize_surface("il"): [entry]},
                entry_meta={1: ("ỉl", "I", "n.", "god")},
                lemma_map={normalize_surface("ỉl"): [entry]},
                entry_stems={},
                entry_gender={},
                udb_words={normalize_udb("il")},
                baseline=None,
                input_format="auto",
                db_checks=True,
                onomastic_override_pos={(normalize_surface("ỉl"), "I"): {"DN m."}},
            )

            disallowed = [
                issue
                for issue in issues
                if issue.message.startswith(
                    "POS token 'DN m. sg. cstr. gen.' not allowed for ỉl (I)"
                )
            ]
            self.assertFalse(disallowed)

    def test_malformed_onomastic_pos_payload_does_not_allow_dn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "auto_parsing" / "0.2.6"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tthm\tthm/\tthm\tDN m. sg. abs. nom.\tthe Ocean\t\n"
                ),
                encoding="utf-8",
            )

            entry = DulatEntry(
                entry_id=1,
                lemma="thm",
                homonym="",
                pos="n.",
                gloss="ocean",
                morph="n. m.",
                form_text="thm",
            )
            issues = lint_file(
                path=path,
                dulat_forms={normalize_surface("thm"): [entry]},
                entry_meta={1: ("thm", "", "n.", "ocean")},
                lemma_map={normalize_surface("thm"): [entry]},
                entry_stems={},
                entry_gender={},
                udb_words={normalize_udb("thm")},
                baseline=None,
                input_format="auto",
                db_checks=True,
                onomastic_override_pos={
                    (normalize_surface("thm"), ""): {"DN m. the Ocean/Primordial Ocean"}
                },
            )

            disallowed = [
                issue
                for issue in issues
                if issue.message.startswith("POS token 'DN m. sg. abs. nom.' not allowed for thm")
            ]
            self.assertTrue(disallowed)


if __name__ == "__main__":
    unittest.main()
