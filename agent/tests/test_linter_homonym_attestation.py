"""Declared homonym indexes must exist in DULAT for the parsed lemma.

Regression source: a reviewed row used the invented homonym `qn(II)` although
DULAT has a single entry `qn` (no homonym split); the linter only raised a
soft surface-match warning.
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lemma_aliases, lint_file, normalize_surface


def _entry(entry_id: int, lemma: str, homonym: str, pos: str, gloss: str) -> DulatEntry:
    return DulatEntry(
        entry_id=entry_id,
        lemma=lemma,
        homonym=homonym,
        pos=pos,
        gloss=gloss,
        morph="",
        form_text=lemma,
    )


def _lint_row(
    surface: str,
    analysis: str,
    dulat_token: str,
    pos_value: str,
    entries: list[DulatEntry],
) -> list:
    header = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
    row = f"1\t{surface}\t{analysis}\t{dulat_token}\t{pos_value}\tgloss\t\n"
    forms_key = normalize_surface(surface)
    lemma_key = normalize_surface(entries[0].lemma)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.7"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "KTU 1.test.tsv"
        path.write_text(header + row, encoding="utf-8")
        return lint_file(
            path=path,
            dulat_forms={forms_key: entries},
            entry_meta={e.entry_id: (e.lemma, e.homonym, e.pos, e.gloss) for e in entries},
            lemma_map={lemma_key: entries},
            entry_stems={},
            entry_gender={},
            udb_words=None,
            baseline=None,
            input_format="auto",
            db_checks=True,
        )


class LinterHomonymAttestationTest(unittest.TestCase):
    def test_dulat_initial_consonant_alternation_supplies_lemma_aliases(self) -> None:
        self.assertEqual(lemma_aliases("s:śkn"), ["s:śkn", "skn", "śkn"])

    def test_invented_homonym_is_error(self) -> None:
        issues = _lint_row(
            surface="qn",
            analysis="qn(II)/",
            dulat_token="qn",
            pos_value="n. m. sg.",
            entries=[_entry(1, "qn", "", "n.", "cane")],
        )
        hits = [(x.level, x.message) for x in issues if x.message.startswith("Declared homonym")]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][0], "error")
        self.assertIn("(II)", hits[0][1])

    def test_attested_homonym_passes(self) -> None:
        issues = _lint_row(
            surface="dgn",
            analysis="dgn(II)/",
            dulat_token="dgn (II)",
            pos_value="DN m. sg. abs. gen.",
            entries=[
                _entry(1, "dgn", "I", "n.", "grain"),
                _entry(2, "dgn", "II", "DN", "Dagan"),
            ],
        )
        hits = [x for x in issues if x.message.startswith("Declared homonym")]
        self.assertFalse(hits)


if __name__ == "__main__":
    unittest.main()
