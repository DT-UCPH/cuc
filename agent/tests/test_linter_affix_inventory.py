"""Affix-inventory validation for +pronominal and ~enclitic segments.

Regression source: KTU 1.5/1.6 auto-parsing marked plural/enclitic -m as a
pronominal suffix (`mrġṯ/+m(I)`, `arṣ/+m(I)`, `yrḫ/+m(I)`), although `+m` is
not part of the pronominal-suffix paradigm in Tagging conventions.
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import invalid_affix_segments, lint_file


class InvalidAffixSegmentsTest(unittest.TestCase):
    def test_pseudo_suffix_m_is_flagged(self) -> None:
        self.assertEqual(invalid_affix_segments("mrġṯ/+m(I)"), [("+", "+m(I)")])
        self.assertEqual(invalid_affix_segments("arṣ/+m(I)"), [("+", "+m(I)")])

    def test_known_pronominal_suffixes_pass(self) -> None:
        for analysis in (
            "mlk/+h",
            "l(I)+y",
            "ˤm(I)+nh=",
            "pn(m/+k",
            "bn(I)/+k",
            "ġlm/+k",
            "!t!št[+nn",
            "!t!kbd[+nh:d",
            "ˤrp(t/t+k",
        ):
            self.assertEqual(invalid_affix_segments(analysis), [], analysis)

    def test_known_enclitics_pass(self) -> None:
        for analysis in (
            "bˤl(II)/~m",
            "g/~m",
            "ṯm~m",
            "ˤd(I)~k",
            "!y!ˤtq[~n",
            "bl(I)~t",
            "aḫ(I)/+y~m",
        ):
            self.assertEqual(invalid_affix_segments(analysis), [], analysis)

    def test_unknown_enclitic_is_flagged(self) -> None:
        self.assertEqual(invalid_affix_segments("g/~q"), [("~", "~q")])

    def test_segments_with_reconstruction_marks_are_skipped(self) -> None:
        # Energic+suffix fusions and reconstructed payloads are shaped by the
        # reconstruction checks, not the inventory check.
        self.assertEqual(invalid_affix_segments("!t!l(ʔ&u(y(I)[~+(n&an"), [])

    def test_placeholder_rows_are_skipped(self) -> None:
        self.assertEqual(invalid_affix_segments("?"), [])
        self.assertEqual(invalid_affix_segments(""), [])

    def test_suffix_stops_at_structured_multiword_boundary(self) -> None:
        self.assertEqual(invalid_affix_segments("uṣbˤ(t/t=+h ˤd(I)"), [])


class LinterAffixInventoryIntegrationTest(unittest.TestCase):
    def test_pseudo_suffix_row_is_error(self) -> None:
        header = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
        row = "1\tmrġṯm\tmrġṯ/+m(I)\tmrġṯ\tn. m.\tsuckling\t\n"
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.7"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(header + row, encoding="utf-8")
            issues = lint_file(
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
        affix_issues = [
            (x.level, x.message) for x in issues if "not in the affix inventory" in x.message
        ]
        self.assertEqual(
            affix_issues,
            [
                (
                    "error",
                    "Suffix segment '+m(I)' is not in the affix inventory (pronominal suffixes)",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
