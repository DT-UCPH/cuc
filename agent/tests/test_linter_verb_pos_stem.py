"""Regression tests for verb POS stem labels in column 5."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterVerbPosStemTest(unittest.TestCase):
    WARNING = "Verb POS should include stem label(s):"
    POS_ERROR = "POS token '"
    MISSING_STEM_MARKER = "Verb stem marker(s) required by POS but missing in analysis:"
    MISSING_N_ASSIMILATION = "Prefixed N-stem forms should encode assimilated nun as '](n]'"

    def _lint_messages(
        self,
        pos_value: str,
        *,
        surface: str = "ytn",
        analysis: str = "!y!ytn[",
        dulat_token: str = "/y-t-n/",
        gloss: str = "to give",
        entry_morph: str = "G, prefc.",
        entry_stems_value: set[str] | None = None,
    ) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "out"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    f"1\t{surface}\t{analysis}\t{dulat_token}\t{pos_value}\t{gloss}\t\n"
                ),
                encoding="utf-8",
            )

            ytn_entry = DulatEntry(
                entry_id=1,
                lemma=dulat_token,
                homonym="",
                pos="vb",
                gloss=gloss,
                morph=entry_morph,
                form_text=surface,
            )

            dulat_forms = {normalize_surface(surface): [ytn_entry]}
            entry_meta = {1: (dulat_token, "", "vb", gloss)}
            lemma_map = {normalize_surface(dulat_token): [ytn_entry]}
            entry_stems = {1: entry_stems_value or {"G"}}
            entry_gender = {}
            udb_words = {normalize_udb(surface)}

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

    def test_warns_when_verb_pos_has_no_stem(self) -> None:
        messages = self._lint_messages("vb")
        self.assertTrue(any(message.startswith(self.WARNING) for message in messages))

    def test_no_warning_when_verb_pos_has_stem(self) -> None:
        messages = self._lint_messages("vb G")
        self.assertFalse(any(message.startswith(self.WARNING) for message in messages))

    def test_vb_stem_pos_is_accepted_by_dulat_pos_validation(self) -> None:
        messages = self._lint_messages("vb G")
        self.assertFalse(any(message.startswith(self.POS_ERROR) for message in messages))

    def test_vb_stem_alternation_is_accepted_by_dulat_pos_validation(self) -> None:
        messages = self._lint_messages("vb G/D")
        self.assertFalse(any(message.startswith(self.POS_ERROR) for message in messages))

    def test_errors_when_pos_requires_d_marker(self) -> None:
        messages = self._lint_messages(
            "vb D",
            surface="kbd",
            analysis="kbd[",
            dulat_token="/k-b-d/",
            gloss="to honour",
            entry_morph="D, prefc.",
            entry_stems_value={"D"},
        )
        self.assertTrue(any(message.startswith(self.MISSING_STEM_MARKER) for message in messages))

    def test_no_error_when_required_d_marker_is_present(self) -> None:
        messages = self._lint_messages(
            "vb D",
            surface="kbd",
            analysis="kbd[:d",
            dulat_token="/k-b-d/",
            gloss="to honour",
            entry_morph="D, prefc.",
            entry_stems_value={"D"},
        )
        self.assertFalse(any(message.startswith(self.MISSING_STEM_MARKER) for message in messages))

    def test_errors_when_prefixed_n_stem_lacks_assimilated_n_marker(self) -> None:
        messages = self._lint_messages(
            "vb N",
            surface="tṯbr",
            analysis="!t!ṯbr[",
            dulat_token="/ṯ-b-r/",
            gloss="to break",
            entry_morph="N, prefc.",
            entry_stems_value={"N"},
        )
        self.assertTrue(
            any(message.startswith(self.MISSING_N_ASSIMILATION) for message in messages)
        )

    def test_no_error_when_prefixed_n_stem_has_assimilated_n_marker(self) -> None:
        messages = self._lint_messages(
            "vb N",
            surface="tṯbr",
            analysis="!t!](n]ṯbr[",
            dulat_token="/ṯ-b-r/",
            gloss="to break",
            entry_morph="N, prefc.",
            entry_stems_value={"N"},
        )
        self.assertFalse(
            any(message.startswith(self.MISSING_N_ASSIMILATION) for message in messages)
        )

    def test_errors_when_aleph_prefixed_n_stem_lacks_assimilated_n_marker(self) -> None:
        messages = self._lint_messages(
            "vb N",
            surface="aṯbr",
            analysis="!(ʔ&a!ṯbr[",
            dulat_token="/ṯ-b-r/",
            gloss="to break",
            entry_morph="N, prefc.",
            entry_stems_value={"N"},
        )
        self.assertTrue(
            any(message.startswith(self.MISSING_N_ASSIMILATION) for message in messages)
        )

    def test_no_error_when_aleph_prefixed_n_stem_has_assimilated_n_marker(self) -> None:
        messages = self._lint_messages(
            "vb N",
            surface="aṯbr",
            analysis="!(ʔ&a!](n]ṯbr[",
            dulat_token="/ṯ-b-r/",
            gloss="to break",
            entry_morph="N, prefc.",
            entry_stems_value={"N"},
        )
        self.assertFalse(
            any(message.startswith(self.MISSING_N_ASSIMILATION) for message in messages)
        )


if __name__ == "__main__":
    unittest.main()
