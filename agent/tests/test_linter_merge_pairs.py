"""Validation of MERGE WITH THE NEXT / PREVIOUS annotation pairs.

Reviewed tablets mark words split across physical lines (e.g. KTU 1.5 VI:3-4
sbn+y = sbny) with paired comments carrying one shared analysis. The linter
must validate the pairing instead of flagging each half as a reconstruction
failure.
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file


class LinterMergePairsTest(unittest.TestCase):
    def _lint_rows(self, rows: list[tuple[str, str, str, str, str, str, str]]) -> list:
        """Lint a synthetic labeled file built from (id, surface, analysis,
        dulat, pos, gloss, comment) rows and return the issue list."""
        header = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
        body = "".join("\t".join(row) + "\n" for row in rows)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.7"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(header + "# KTU 1.5 VI:3\t\t\t\t\t\t\n" + body, encoding="utf-8")
            return lint_file(
                path=path,
                dulat_forms={},
                entry_meta={},
                lemma_map={},
                entry_stems={},
                entry_gender={},
                udb_words=None,
                baseline=None,
                input_format="auto",
                db_checks=False,
            )

    @staticmethod
    def _messages(issues, prefix: str) -> list[tuple[str, str]]:
        return [(x.level, x.message) for x in issues if x.message.startswith(prefix)]

    def test_valid_merge_pair_has_no_reconstruction_or_pairing_issues(self) -> None:
        issues = self._lint_rows(
            [
                (
                    "1",
                    "sbn",
                    "sb(b[ny",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. du.",
                    "to go around",
                    "MERGE WITH THE NEXT: sbn+y = sbny, split across lines VI:3/4.",
                ),
                (
                    "2",
                    "y",
                    "sb(b[ny",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. du.",
                    "to go around",
                    "MERGE WITH THE PREVIOUS.",
                ),
            ]
        )
        self.assertFalse(self._messages(issues, "Analysis does not reconstruct to surface"))
        self.assertFalse(self._messages(issues, "MERGE"))
        self.assertFalse(self._messages(issues, "Merged analysis"))
        self.assertFalse(
            [x for x in issues if "TODO/uncertain marker" in x.message],
            "structured MERGE annotations must not raise the TODO 'merge' warning",
        )

    def test_merge_next_without_partner_is_error(self) -> None:
        issues = self._lint_rows(
            [
                (
                    "1",
                    "sbn",
                    "sb(b[ny",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. du.",
                    "to go around",
                    "MERGE WITH THE NEXT: sbn+y = sbny.",
                ),
                ("2", "y", "y", "y", "voc. functor", "oh!", ""),
            ]
        )
        merge_issues = self._messages(issues, "MERGE WITH THE NEXT")
        self.assertTrue(merge_issues)
        self.assertTrue(all(level == "error" for level, _ in merge_issues))

    def test_merge_previous_without_partner_is_error(self) -> None:
        issues = self._lint_rows(
            [
                ("1", "sbn", "sb(b[n", "/s:ś-b-b/", "vb G suffc. 1 c. pl.", "to go around", ""),
                (
                    "2",
                    "y",
                    "sb(b[ny",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. du.",
                    "to go around",
                    "MERGE WITH THE PREVIOUS.",
                ),
            ]
        )
        merge_issues = self._messages(issues, "MERGE WITH THE PREVIOUS")
        self.assertTrue(merge_issues)
        self.assertTrue(all(level == "error" for level, _ in merge_issues))

    def test_merge_pair_with_mismatched_analyses_is_error(self) -> None:
        issues = self._lint_rows(
            [
                (
                    "1",
                    "sbn",
                    "sb(b[ny",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. du.",
                    "to go around",
                    "MERGE WITH THE NEXT.",
                ),
                (
                    "2",
                    "y",
                    "sb(b[n",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. pl.",
                    "to go around",
                    "MERGE WITH THE PREVIOUS.",
                ),
            ]
        )
        mismatch = self._messages(issues, "MERGE pair carries different analyses")
        self.assertTrue(mismatch)
        self.assertTrue(all(level == "error" for level, _ in mismatch))

    def test_merge_pair_joint_reconstruction_failure_is_error(self) -> None:
        issues = self._lint_rows(
            [
                (
                    "1",
                    "sbn",
                    "sb(b[nyy",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. du.",
                    "to go around",
                    "MERGE WITH THE NEXT.",
                ),
                (
                    "2",
                    "y",
                    "sb(b[nyy",
                    "/s:ś-b-b/",
                    "vb G suffc. 1 c. du.",
                    "to go around",
                    "MERGE WITH THE PREVIOUS.",
                ),
            ]
        )
        joint = self._messages(issues, "Merged analysis does not reconstruct")
        self.assertTrue(joint)
        self.assertTrue(all(level == "error" for level, _ in joint))


if __name__ == "__main__":
    unittest.main()
