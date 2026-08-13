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
        generic_override_analyses: dict[str, set[str]] | None = None,
        entry_stems: dict[int, set[str]] | None = None,
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
                entry_stems=entry_stems or {},
                entry_gender={},
                udb_words={normalize_udb(surface)},
                baseline=None,
                input_format="auto",
                db_checks=True,
                generic_override_lexemes=generic_override_lexemes,
                generic_override_analyses=generic_override_analyses,
            )
            return [(issue.level, issue.message) for issue in issues]

    def _reconstruction_levels(self, messages: list[tuple[str, str]]) -> list[str]:
        return [
            level
            for level, message in messages
            if message.startswith("Analysis does not reconstruct to surface")
        ]

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
            generic_override_analyses={"y": {"yy"}},
        )
        mismatch_levels = self._reconstruction_levels(messages)
        self.assertTrue(mismatch_levels)
        self.assertTrue(all(level == "info" for level in mismatch_levels))

    def test_reconstructability_error_stays_error_without_whitelisted_analysis(self) -> None:
        """A lexeme-key intersection alone must not demote reconstruction errors.

        Regression for KTU 1.5 V:12 ttn parsed as `ytn[`: the override row for
        surface `tn` whitelists `(ytn[`, but `ttn`/`ytn[` is a genuine parser
        error and must stay at error level.
        """
        entry = DulatEntry(
            entry_id=1,
            lemma="/y-t-n/",
            homonym="",
            pos="vb",
            gloss="to give",
            morph="G, prefc.",
            form_text="ytn",
        )
        messages = self._lint_messages(
            surface="ttn",
            analysis="ytn[",
            dulat_token="/y-t-n/",
            pos_value="vb G prefc. 2 m. sg.",
            gloss="to give",
            dulat_forms={normalize_surface("ytn"): [entry]},
            entry_meta={1: ("/y-t-n/", "", "vb", "to give")},
            lemma_map={normalize_surface("/y-t-n/"): [entry]},
            generic_override_lexemes={"tn", "ytn", "y-t-n"},
            generic_override_analyses={"tn": {"(ytn[", "(ytn[/"}},
        )
        mismatch_levels = self._reconstruction_levels(messages)
        self.assertTrue(mismatch_levels)
        self.assertTrue(all(level == "error" for level in mismatch_levels))

    def test_reconstructability_error_stays_error_for_foreign_surface(self) -> None:
        """Cross-token leakage (gh parsed as ytn[) must stay at error level."""
        entry = DulatEntry(
            entry_id=1,
            lemma="/y-t-n/",
            homonym="",
            pos="vb",
            gloss="to give",
            morph="G, prefc.",
            form_text="ytn",
        )
        messages = self._lint_messages(
            surface="gh",
            analysis="ytn[",
            dulat_token="/y-t-n/",
            pos_value="vb",
            gloss="to give",
            dulat_forms={normalize_surface("ytn"): [entry]},
            entry_meta={1: ("/y-t-n/", "", "vb", "to give")},
            lemma_map={normalize_surface("/y-t-n/"): [entry]},
            generic_override_lexemes={"tn", "ytn", "y-t-n"},
            generic_override_analyses={"tn": {"(ytn[", "(ytn[/"}},
        )
        mismatch_levels = self._reconstruction_levels(messages)
        self.assertTrue(mismatch_levels)
        self.assertTrue(all(level == "error" for level in mismatch_levels))

    def test_stem_discrepancy_is_info_for_exact_override_pair(self) -> None:
        entry = DulatEntry(
            entry_id=1,
            lemma="/y/w-ḥ-l/",
            homonym="",
            pos="vb",
            gloss="to be worried",
            morph="G, prefc.",
            form_text="twḥln",
        )
        messages = self._lint_messages(
            surface="twḥln",
            analysis="!t!wḥl[:d~n",
            dulat_token="/y/w-ḥ-l/",
            pos_value="vb D prefc. 2 f. sg. + encl. -n",
            gloss="to be worried",
            dulat_forms={normalize_surface("twḥln"): [entry]},
            entry_meta={1: ("/y/w-ḥ-l/", "", "vb", "to be worried")},
            lemma_map={
                normalize_surface("/y/w-ḥ-l/"): [entry],
                normalize_surface("/w-ḥ-l/"): [entry],
            },
            entry_stems={1: {"G"}},
            generic_override_lexemes={"twḥln", "y/w-ḥ-l", "ywḥl"},
            generic_override_analyses={"twḥln": {"!t!wḥl[:d~n"}},
        )
        levels = [
            level
            for level, message in messages
            if message == "D stem marker present but DULAT lacks D/Dt/tD"
        ]
        self.assertEqual(levels, ["info"])

    def test_stem_discrepancy_stays_error_for_unlisted_analysis(self) -> None:
        entry = DulatEntry(
            entry_id=1,
            lemma="/y/w-ḥ-l/",
            homonym="",
            pos="vb",
            gloss="to be worried",
            morph="G, prefc.",
            form_text="twḥln",
        )
        messages = self._lint_messages(
            surface="twḥln",
            analysis="!t!wḥl[:d:pass~n",
            dulat_token="/y/w-ḥ-l/",
            pos_value="vb Dpass prefc. 2 f. sg. + encl. -n",
            gloss="to be worried",
            dulat_forms={normalize_surface("twḥln"): [entry]},
            entry_meta={1: ("/y/w-ḥ-l/", "", "vb", "to be worried")},
            lemma_map={
                normalize_surface("/y/w-ḥ-l/"): [entry],
                normalize_surface("/w-ḥ-l/"): [entry],
            },
            entry_stems={1: {"G"}},
            generic_override_lexemes={"twḥln", "y/w-ḥ-l", "ywḥl"},
            generic_override_analyses={"twḥln": {"!t!wḥl[:d~n"}},
        )
        levels = [
            level
            for level, message in messages
            if message
            in {
                "D stem marker present but DULAT lacks D/Dt/tD",
                "Passive stem marker present but DULAT lacks passive/N stem",
            }
        ]
        self.assertEqual(levels, ["error", "error"])

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
            if message.startswith("No DULAT entry found for clitic part: y")
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

    def test_comment_mismatch_is_info_for_generic_override_lexeme(self) -> None:
        entry_surface = DulatEntry(
            entry_id=1,
            lemma="y",
            homonym="I",
            pos="prep.",
            gloss="oh!",
            morph="",
            form_text="y",
        )
        entry_suffix = DulatEntry(
            entry_id=2,
            lemma="-y",
            homonym="I",
            pos="postp.",
            gloss="indeed",
            morph="",
            form_text="y",
        )
        messages = self._lint_messages(
            surface="y",
            analysis="~y",
            dulat_token="-y (II)",
            pos_value="prep. functor",
            gloss="indeed",
            dulat_forms={normalize_surface("y"): [entry_surface, entry_suffix]},
            entry_meta={
                1: ("y", "I", "prep.", "oh!"),
                2: ("-y", "I", "postp.", "indeed"),
            },
            lemma_map={
                normalize_surface("y"): [entry_surface],
                normalize_surface("-y"): [entry_suffix],
            },
            generic_override_lexemes={"y", "-y"},
        )
        levels = [
            level
            for level, message in messages
            if message.startswith("DULAT comment") and "not in candidates" in message
        ]
        self.assertTrue(levels)
        self.assertTrue(all(level == "info" for level in levels))

    def test_comment_mismatch_stays_error_for_non_standalone_override_analysis(self) -> None:
        entry_one = DulatEntry(
            entry_id=1,
            lemma="foo",
            homonym="",
            pos="n.",
            gloss="x",
            morph="",
            form_text="ar",
        )
        entry_two = DulatEntry(
            entry_id=2,
            lemma="bar",
            homonym="",
            pos="n.",
            gloss="y",
            morph="",
            form_text="ar",
        )
        messages = self._lint_messages(
            surface="ar",
            analysis="a/r",
            dulat_token="baz",
            pos_value="n.",
            gloss="z",
            dulat_forms={normalize_surface("ar"): [entry_one, entry_two]},
            entry_meta={1: ("foo", "", "n.", "x"), 2: ("bar", "", "n.", "y")},
            lemma_map={
                normalize_surface("foo"): [entry_one],
                normalize_surface("bar"): [entry_two],
            },
            generic_override_lexemes={"a", "ar", "baz"},
        )
        levels = [
            level
            for level, message in messages
            if message.startswith("DULAT comment") and "not in candidates" in message
        ]
        self.assertTrue(levels)
        self.assertTrue(all(level == "error" for level in levels))

    def test_comment_mismatch_is_info_for_exact_non_standalone_override(self) -> None:
        entry_one = DulatEntry(
            entry_id=1,
            lemma="foo",
            homonym="",
            pos="n.",
            gloss="x",
            morph="",
            form_text="ar",
        )
        entry_two = DulatEntry(
            entry_id=2,
            lemma="bar",
            homonym="",
            pos="n.",
            gloss="y",
            morph="",
            form_text="ar",
        )
        messages = self._lint_messages(
            surface="ar",
            analysis="a/r",
            dulat_token="baz",
            pos_value="n.",
            gloss="z",
            dulat_forms={normalize_surface("ar"): [entry_one, entry_two]},
            entry_meta={1: ("foo", "", "n.", "x"), 2: ("bar", "", "n.", "y")},
            lemma_map={
                normalize_surface("foo"): [entry_one],
                normalize_surface("bar"): [entry_two],
            },
            generic_override_lexemes={"a", "ar", "baz"},
            generic_override_analyses={"ar": {"a/r"}},
        )
        levels = [
            level
            for level, message in messages
            if message.startswith("DULAT comment") and "not in candidates" in message
        ]
        self.assertEqual(levels, ["info"])

    def test_missing_column_4_tokens_is_info_for_generic_override_lexeme(self) -> None:
        messages = self._lint_messages(
            surface="t",
            analysis="/t",
            dulat_token="",
            pos_value="",
            gloss="",
            dulat_forms={},
            entry_meta={},
            lemma_map={},
            generic_override_lexemes={"t", "-t"},
        )
        levels = [
            level
            for level, message in messages
            if message == "Missing DULAT entry token(s) in column 4"
        ]
        self.assertTrue(levels)
        self.assertTrue(all(level == "info" for level in levels))

    def test_duplicate_feature_bundle_is_info_for_generic_override_lexeme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            out_dir = root / "auto_parsing" / "0.2.6"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tt\t/t\t\t\t\t\n"
                    "1\tt\t[t\t\t\t\t\n"
                ),
                encoding="utf-8",
            )
            issues = lint_file(
                path=path,
                dulat_forms={},
                entry_meta={},
                lemma_map={},
                entry_stems={},
                entry_gender={},
                udb_words={normalize_udb("t")},
                baseline=None,
                input_format="auto",
                db_checks=True,
                generic_override_lexemes={"t", "-t"},
            )
        levels = [
            issue.level
            for issue in issues
            if issue.message.startswith("Duplicate feature bundle with different analysis")
        ]
        self.assertTrue(levels)
        self.assertTrue(all(level == "info" for level in levels))


if __name__ == "__main__":
    unittest.main()
