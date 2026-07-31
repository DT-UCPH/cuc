"""Linter support for multiple words joined into one Text-Fabric token."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file, normalize_surface


def _entry(entry_id: int, lemma: str, homonym: str, pos: str) -> DulatEntry:
    return DulatEntry(
        entry_id=entry_id,
        lemma=lemma,
        homonym=homonym,
        pos=pos,
        gloss=lemma,
        morph="",
        form_text=lemma,
    )


def _lint(row: str, entries: list[DulatEntry]) -> list:
    header = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
    lemma_map: dict[str, list[DulatEntry]] = {}
    for entry in entries:
        lemma_map.setdefault(normalize_surface(entry.lemma), []).append(entry)
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "reviewed" / "KTU 1.test.tsv"
        path.parent.mkdir()
        path.write_text(header + row, encoding="utf-8")
        return lint_file(
            path=path,
            dulat_forms={},
            entry_meta={
                entry.entry_id: (entry.lemma, entry.homonym, entry.pos, entry.gloss)
                for entry in entries
            },
            lemma_map=lemma_map,
            entry_stems={},
            entry_gender={},
            udb_words=None,
            baseline=None,
            input_format="auto",
            db_checks=True,
        )


class LinterMultiwordTokensTest(unittest.TestCase):
    def test_validates_each_word_without_whole_surface_lookup(self) -> None:
        issues = _lint(
            "1\tpblmlk\tpbl/ mlk(I)/\tpbl, mlk (I)\t"
            "PN, n. m. sg. abs. gen.\tPabilu, king\tjoined by TF\n",
            [
                _entry(1, "pbl", "", "PN"),
                _entry(2, "mlk", "I", "n."),
            ],
        )
        messages = [issue.message for issue in issues]
        self.assertFalse(any(message.startswith("Declared homonym") for message in messages))
        self.assertNotIn("No DULAT entry found for lexeme/surface", messages)
        self.assertFalse(any(message.startswith("Unknown DULAT token") for message in messages))
        self.assertFalse(any(message.startswith("POS grammar") for message in messages))

    def test_unknown_component_remains_an_error(self) -> None:
        issues = _lint(
            "1\tpblzzz\tpbl/ zzz/\tpbl, zzz\tPN, n. m.\tPabilu, unknown\t\n",
            [_entry(1, "pbl", "", "PN")],
        )
        self.assertTrue(any(issue.message == "Unknown DULAT token in column 4: zzz" for issue in issues))

    def test_single_word_bad_homonym_still_uses_global_validation(self) -> None:
        issues = _lint(
            "1\tmlk\tmlk(II)/\tmlk (II)\tn. m.\tking\t\n",
            [_entry(1, "mlk", "I", "n.")],
        )
        self.assertTrue(any(issue.message.startswith("Declared homonym (II)") for issue in issues))


if __name__ == "__main__":
    unittest.main()
