"""Regression tests for suffix payload linkage warnings in linter."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb

SUFFIX_PAYLOAD_MSG = (
    "For clitic-bearing analyses, keep suffix/enclitic in col3 only; "
    "do not use ', -x' suffix payload in DULAT col4"
)


class LinterSuffixPayloadWarningTest(unittest.TestCase):
    def _run_lint(self, analysis: str, dulat: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    f"1\tgh\t{analysis}\t{dulat}\tn. m.\t(loud) voice\t\n"
                ),
                encoding="utf-8",
            )

            entry = DulatEntry(
                entry_id=1,
                lemma="g",
                homonym="",
                pos="n. m.",
                gloss="(loud) voice",
                morph="sg.",
                form_text="gh",
            )
            dulat_forms = {normalize_surface("gh"): [entry]}
            entry_meta = {1: ("g", "", "n. m.", "(loud) voice")}
            lemma_map = {normalize_surface("g"): [entry]}
            entry_stems = {}
            entry_gender = {}
            udb_words = {normalize_udb("gh")}

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
            return [issue.message for issue in issues]

    def test_warns_for_suffix_payload_linkage(self) -> None:
        msgs = self._run_lint(analysis="g/+h", dulat="g, -h (I)")
        self.assertIn(SUFFIX_PAYLOAD_MSG, msgs)

    def test_no_warning_for_host_only_dulat(self) -> None:
        msgs = self._run_lint(analysis="g/+h", dulat="g")
        self.assertNotIn(SUFFIX_PAYLOAD_MSG, msgs)


if __name__ == "__main__":
    unittest.main()
