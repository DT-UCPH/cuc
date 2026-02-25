"""Regression tests for infinitive and participle analysis encoding."""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface, normalize_udb


class LinterInfinitiveEncodingTest(unittest.TestCase):
    INF_WARNING = "Infinitive should use `!!...[/` analysis encoding"
    PTCP_WARNING = "Participles should not use infinitive marker `!!`"

    def _lint_messages(
        self,
        *,
        surface: str,
        analysis: str,
        dulat_token: str,
        pos_value: str,
        gloss: str,
        entry_morph: str,
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

            entry = DulatEntry(
                entry_id=1,
                lemma=dulat_token,
                homonym="",
                pos="vb",
                gloss=gloss,
                morph=entry_morph,
                form_text=surface,
            )
            dulat_forms = {normalize_surface(surface): [entry]}
            entry_meta = {1: (dulat_token, "", "vb", gloss)}
            lemma_map = {normalize_surface(dulat_token): [entry]}
            entry_stems = {1: {"G"}}
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

    def test_warns_when_infinitive_lacks_double_bang_marker(self) -> None:
        messages = self._lint_messages(
            surface="ṯny",
            analysis="ṯny[/",
            dulat_token="/ṯ-n-y/",
            pos_value="vb G inf.",
            gloss="to repeat",
            entry_morph="G, inf.",
        )
        self.assertTrue(any(message.startswith(self.INF_WARNING) for message in messages))

    def test_accepts_infinitive_with_double_bang_marker(self) -> None:
        messages = self._lint_messages(
            surface="ṯny",
            analysis="!!ṯny[/",
            dulat_token="/ṯ-n-y/",
            pos_value="vb G inf.",
            gloss="to repeat",
            entry_morph="G, inf.",
        )
        self.assertFalse(any(message.startswith(self.INF_WARNING) for message in messages))

    def test_warns_when_participle_uses_double_bang_marker(self) -> None:
        messages = self._lint_messages(
            surface="qtl",
            analysis="!!qtl[/",
            dulat_token="/q-t-l/",
            pos_value="vb G pass. ptcpl.",
            gloss="killed",
            entry_morph="G, pass. ptcpl.",
        )
        self.assertTrue(any(message.startswith(self.PTCP_WARNING) for message in messages))


if __name__ == "__main__":
    unittest.main()
