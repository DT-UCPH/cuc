"""Regression tests for linter plurale-tantum -m noun checks."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterPluraleTantumMRuleTest(unittest.TestCase):
    def _run_lint(self, pos_value: str) -> list:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    f"1\tpnwh\tpn&w(m/+h\tpnm\t{pos_value}\tface\t\n"
                ),
                encoding="utf-8",
            )

            entry_pl = DulatEntry(
                entry_id=1,
                lemma="pnm",
                homonym="",
                pos="n.",
                gloss="face",
                morph="pl.",
                form_text="pnm",
            )
            entry_suff = DulatEntry(
                entry_id=1,
                lemma="pnm",
                homonym="",
                pos="n.",
                gloss="face",
                morph="suff.",
                form_text="pnwh",
            )
            dulat_forms = {
                normalize_surface("pnm"): [entry_pl],
                normalize_surface("pnwh"): [entry_suff],
            }
            entry_meta = {1: ("pnm", "", "n.", "face")}
            lemma_map = {normalize_surface("pnm"): [entry_pl]}
            entry_stems = {}
            entry_gender = {1: "m."}
            udb_words = {normalize_udb("pnwh")}

            return lint_file(
                path=path,
                dulat_forms=dulat_forms,
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems=entry_stems,
                entry_gender=entry_gender,
                udb_words=udb_words,
                baseline=None,
                input_format="auto",
                db_checks=True,
            )

    def test_does_not_warn_when_pos_has_plurale_tantum_marker(self) -> None:
        issues = self._run_lint("n. m. pl. tant.")
        messages = [item.message for item in issues]
        self.assertNotIn(
            "DULAT plurale tantum noun should include 'pl. tant.' in POS",
            messages,
        )

    def test_warns_when_pos_lacks_plurale_tantum_marker(self) -> None:
        issues = self._run_lint("n. m.")
        messages = [item.message for item in issues]
        self.assertIn(
            "DULAT plurale tantum noun should include 'pl. tant.' in POS",
            messages,
        )

    def test_does_not_require_pl_tant_for_sg_suffix_lemma(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tšlmm\tšlm(II)/~m; šlm(II)/m\tšlm (II); šlm (II)\tn. m.; n. m.\t"
                    "communion victim / sacrifice; communion victim / sacrifice\t\n"
                ),
                encoding="utf-8",
            )

            entry_pl = DulatEntry(
                entry_id=1,
                lemma="šlm",
                homonym="II",
                pos="n.",
                gloss="communion victim / sacrifice",
                morph="pl.",
                form_text="šlmm",
            )
            entry_sg_suff = DulatEntry(
                entry_id=1,
                lemma="šlm",
                homonym="II",
                pos="n.",
                gloss="communion victim / sacrifice",
                morph="sg., suff.",
                form_text="šlmm",
            )
            dulat_forms = {
                normalize_surface("šlmm"): [entry_pl, entry_sg_suff],
            }
            entry_meta = {1: ("šlm", "II", "n.", "communion victim / sacrifice")}
            lemma_map = {normalize_surface("šlm"): [entry_pl]}
            entry_stems = {}
            entry_gender = {1: "m."}
            udb_words = {normalize_udb("šlmm")}

            issues = lint_file(
                path=path,
                dulat_forms=dulat_forms,
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems=entry_stems,
                entry_gender=entry_gender,
                udb_words=udb_words,
                baseline=None,
                input_format="auto",
                db_checks=True,
            )
            messages = [item.message for item in issues]
            self.assertNotIn(
                "DULAT plurale tantum noun should include 'pl. tant.' in POS",
                messages,
            )

    def test_does_not_require_pl_tant_for_cst_only_plural_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tqm\tqm/\tqm\tn. m.\tadversary\t\n"
                ),
                encoding="utf-8",
            )

            entry_qm = DulatEntry(
                entry_id=1,
                lemma="qm",
                homonym="",
                pos="n.",
                gloss="adversary",
                morph="pl., cst.",
                form_text="qm",
            )
            dulat_forms = {normalize_surface("qm"): [entry_qm]}
            entry_meta = {1: ("qm", "", "n.", "adversary")}
            lemma_map = {normalize_surface("qm"): [entry_qm]}
            entry_stems = {}
            entry_gender = {1: "m."}
            udb_words = {normalize_udb("qm")}

            issues = lint_file(
                path=path,
                dulat_forms=dulat_forms,
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems=entry_stems,
                entry_gender=entry_gender,
                udb_words=udb_words,
                baseline=None,
                input_format="auto",
                db_checks=True,
            )
            messages = [item.message for item in issues]
            self.assertNotIn(
                "DULAT plurale tantum noun should include 'pl. tant.' in POS",
                messages,
            )

    def test_does_not_require_pl_tant_for_curated_plural_m_exclusions(self) -> None:
        cases = [
            (
                "ḥlmm",
                "ḥlm(II)/m",
                "ḥlm (II)",
                1,
                ("ḥlm", "II"),
                "pl.",
            ),
            (
                "ʕgmm",
                "ʕgm/m",
                "ʕgm",
                2,
                ("ʕgm", ""),
                "pl.",
            ),
            (
                "ỉštnm",
                "ištnm/",
                "ỉštnm",
                3,
                ("ỉštnm", ""),
                "pl.",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"

            data_lines = ["id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments"]
            entry_meta = {}
            entry_gender = {}
            dulat_forms = {}
            lemma_map = {}
            udb_words = set()

            for surface, analysis, dulat, entry_id, (lemma, hom), morph in cases:
                data_lines.append(f"{entry_id}\t{surface}\t{analysis}\t{dulat}\tn. m.\tlemma\t")
                entry = DulatEntry(
                    entry_id=entry_id,
                    lemma=lemma,
                    homonym=hom,
                    pos="n.",
                    gloss="lemma",
                    morph=morph,
                    form_text=surface,
                )
                dulat_forms.setdefault(normalize_surface(surface), []).append(entry)
                lemma_map.setdefault(normalize_surface(lemma), []).append(entry)
                entry_meta[entry_id] = (lemma, hom, "n.", "lemma")
                entry_gender[entry_id] = "m."
                udb_words.add(normalize_udb(surface))

            path.write_text("\n".join(data_lines) + "\n", encoding="utf-8")

            issues = lint_file(
                path=path,
                dulat_forms=dulat_forms,
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems={},
                entry_gender=entry_gender,
                udb_words=udb_words,
                baseline=None,
                input_format="auto",
                db_checks=True,
            )

            messages = [item.message for item in issues]
            self.assertNotIn(
                "DULAT plurale tantum noun should include 'pl. tant.' in POS",
                messages,
            )


if __name__ == "__main__":
    unittest.main()
