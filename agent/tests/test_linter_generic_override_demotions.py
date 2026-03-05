"""Scoped demotions for generic parsing override lexemes."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterGenericOverrideDemotionsTest(unittest.TestCase):
    def _lint_messages(
        self,
        *,
        surface: str,
        analysis: str,
        dulat_token: str,
        pos_value: str,
        gloss: str,
        dulat_forms: dict[str, list[DulatEntry]],
        entry_meta: dict[int, tuple[str, str, str, str]],
        lemma_map: dict[str, list[DulatEntry]],
        generic_override_lexemes: set[str],
    ) -> list[tuple[str, str]]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "auto_parsing" / "0.2.6"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    f"1\t{surface}\t{analysis}\t{dulat_token}\t{pos_value}\t{gloss}\t\n"
                ),
                encoding="utf-8",
            )

            issues = lint_file(
                path=path,
                dulat_forms=dulat_forms,
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems={},
                entry_gender={},
                udb_words={normalize_udb(surface)},
                baseline=None,
                input_format="auto",
                db_checks=True,
                generic_override_lexemes=generic_override_lexemes,
            )
            return [(issue.level, issue.message) for issue in issues]

    def test_pos_token_not_allowed_is_info_for_generic_override_lexeme(self) -> None:
        entry = DulatEntry(
            entry_id=1,
            lemma="-y",
            homonym="I",
            pos="prep.",
            gloss="my",
            morph="",
            form_text="y",
        )
        messages = self._lint_messages(
            surface="y",
            analysis="y",
            dulat_token="-y (I)",
            pos_value="n.",
            gloss="my",
            dulat_forms={normalize_surface("y"): [entry]},
            entry_meta={1: ("-y", "I", "prep.", "my")},
            lemma_map={normalize_surface("-y"): [entry]},
            generic_override_lexemes={"y", "-y"},
        )
        pos_errors = [
            level
            for level, message in messages
            if message.startswith("POS token 'n.' not allowed for -y (I)")
        ]
        self.assertTrue(pos_errors)
        self.assertTrue(all(level == "info" for level in pos_errors))

    def test_reconstructability_error_is_info_for_generic_override_lexeme(self) -> None:
        entry = DulatEntry(
            entry_id=1,
            lemma="-y",
            homonym="I",
            pos="prep.",
            gloss="my",
            morph="",
            form_text="y",
        )
        messages = self._lint_messages(
            surface="y",
            analysis="yy",
            dulat_token="-y (I)",
            pos_value="prep. functor",
            gloss="my",
            dulat_forms={normalize_surface("y"): [entry]},
            entry_meta={1: ("-y", "I", "prep.", "my")},
            lemma_map={normalize_surface("-y"): [entry]},
            generic_override_lexemes={"y", "-y"},
        )
        mismatch_levels = [
            level
            for level, message in messages
            if message.startswith("Analysis does not reconstruct to surface")
        ]
        self.assertTrue(mismatch_levels)
        self.assertTrue(all(level == "info" for level in mismatch_levels))

    def test_missing_clitic_entry_error_is_info_for_generic_override_lexeme(self) -> None:
        entry = DulatEntry(
            entry_id=1,
            lemma="-y",
            homonym="I",
            pos="prep.",
            gloss="my",
            morph="",
            form_text="y",
        )
        messages = self._lint_messages(
            surface="y",
            analysis="+y, [y",
            dulat_token="-y (I)",
            pos_value="prep. functor",
            gloss="my",
            dulat_forms={normalize_surface("y"): [entry]},
            entry_meta={1: ("-y", "I", "prep.", "my")},
            lemma_map={},
            generic_override_lexemes={"y", "-y"},
        )
        clitic_levels = [
            level
            for level, message in messages
            if message.startswith("No DULAT entry found for clitic part: y, [y")
        ]
        self.assertTrue(clitic_levels)
        self.assertTrue(all(level == "info" for level in clitic_levels))

    def test_missing_lexeme_surface_entry_is_info_for_generic_override_lexeme(self) -> None:
        messages = self._lint_messages(
            surface="n",
            analysis="[n, [n=",
            dulat_token="-n (II)",
            pos_value="vb",
            gloss="me",
            dulat_forms={},
            entry_meta={1: ("-n", "II", "vb", "me")},
            lemma_map={},
            generic_override_lexemes={"n", "-n"},
        )
        levels = [
            level
            for level, message in messages
            if message == "No DULAT entry found for lexeme/surface"
        ]
        self.assertTrue(levels)
        self.assertTrue(all(level == "info" for level in levels))


if __name__ == "__main__":
    unittest.main()
