"""Regression tests for analysis-vs-declared-lemma radical mismatches.

Both columns can be individually valid while contradicting each other: an
analysis spelling mṣḫ resolves to a real DULAT entry, and the declared /m-ṣ-ḥ/
resolves to a different real entry, so neither the DULAT lookup nor the surface
reconstruction notices. Only the equal-length skeleton comparison does.
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lexeme_skeleton, lint_file, normalize_surface

MESSAGE_FRAGMENT = "spells a radical the declared"


def _write(path: Path, analysis: str, dulat: str, surface: str) -> None:
    path.write_text(
        "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
        "1\t%s\t%s\t%s\tvb G prefc. 3 m. sg.\tto pull\t\n" % (surface, analysis, dulat),
        encoding="utf-8",
    )


class LexemeRadicalMismatchTest(unittest.TestCase):
    def _run(self, analysis: str, dulat: str, surface: str, entries):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.6"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            _write(path, analysis, dulat, surface)

            lemma_map = {}
            entry_meta = {}
            for entry in entries:
                lemma_map.setdefault(normalize_surface(entry.lemma), []).append(entry)
                entry_meta[entry.entry_id] = (
                    entry.lemma, entry.homonym, entry.pos, entry.gloss,
                )
            return lint_file(
                path=path,
                dulat_forms={},
                entry_meta=entry_meta,
                lemma_map=lemma_map,
                entry_stems={e.entry_id: {"G"} for e in entries},
                entry_gender={},
                udb_words=set(),
                baseline=None,
                input_format="auto",
                db_checks=True,
            )

    @staticmethod
    def _mṣḥ_entries():
        root = DulatEntry(
            entry_id=1, lemma="/m-ṣ-ḥ/", homonym="", pos="vb",
            gloss="to pull", morph="G, prefc.", form_text="ymṣḥ",
        )
        other = DulatEntry(
            entry_id=2, lemma="mṣḫ", homonym="", pos="vb",
            gloss="to drag down", morph="", form_text="mṣḫ",
        )
        return [root, other]

    def test_unmarked_radical_substitution_is_error(self) -> None:
        issues = self._run("!y!mṣḫ[", "/m-ṣ-ḥ/", "ymṣḫ", self._mṣḥ_entries())
        matches = [i for i in issues if MESSAGE_FRAGMENT in i.message]
        self.assertTrue(matches, "expected the mismatch to be reported")
        self.assertTrue(all(i.level == "error" for i in matches))

    def test_marked_substitution_is_accepted(self) -> None:
        issues = self._run("!y!mṣ(ḥ&ḫ[", "/m-ṣ-ḥ/", "ymṣḫ", self._mṣḥ_entries())
        self.assertFalse([i for i in issues if MESSAGE_FRAGMENT in i.message])

    def test_shorter_analysis_base_is_not_a_mismatch(self) -> None:
        """DULAT lemmatises plurale tantum whole; the analysis base is shorter."""
        entries = [
            DulatEntry(entry_id=1, lemma="ddym", homonym="", pos="n.",
                       gloss="love", morph="n. m. pl.", form_text="ddym"),
            DulatEntry(entry_id=2, lemma="ddy", homonym="", pos="n.",
                       gloss="beloved", morph="n. m.", form_text="ddy"),
        ]
        issues = self._run("ddy/m", "ddym", "ddym", entries)
        self.assertFalse([i for i in issues if MESSAGE_FRAGMENT in i.message])


class LexemeSkeletonTest(unittest.TestCase):
    def test_aleph_spellings_fold_together(self) -> None:
        """sʔd and sỉd are one skeleton, so they must not read as a difference."""
        self.assertEqual(lexeme_skeleton("sʔd"), lexeme_skeleton("sỉd"))

    def test_root_markers_are_stripped(self) -> None:
        self.assertEqual(lexeme_skeleton("/m-ṣ-ḥ/"), lexeme_skeleton("mṣḥ"))

    def test_distinct_radicals_stay_distinct(self) -> None:
        self.assertNotEqual(lexeme_skeleton("mṣḫ"), lexeme_skeleton("/m-ṣ-ḥ/"))

    def test_ayin_spellings_fold_together(self) -> None:
        self.assertEqual(lexeme_skeleton("ʕbd"), lexeme_skeleton("ˤbd"))


if __name__ == "__main__":
    unittest.main()
