import tempfile
import unittest
from pathlib import Path

from linter.lint import lint_file
from pipeline.config.ytb_messenger_readings import YTB_PARTICIPLE_WARNING
from pipeline.steps.ytb_messenger_readings import YtbMessengerReadingPruner


HEADER = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
PTCP = "1\tyṯb\tyṯb[/\t/y-ṯ-b/\tvb G act. ptcpl. m. sg.\tto sit\t"
PREFIX = "1\tyṯb\t!y=!(yṯb[\t/y-ṯ-b/\tvb G prefc. 3 m. du.\tto sit\tTropper"
SUFFIX = "1\tyṯb\tyṯb[\t/y-ṯ-b/\tvb G suffc. 3 m. du.\tto sit\tEUPT"


class YtbMessengerReadingsTest(unittest.TestCase):
    def run_case(self, ref, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "KTU test.tsv"
            original = HEADER + "# " + ref + "\n" + "\n".join(rows) + "\n"
            path.write_text(original, encoding="utf-8")
            issues = lint_file(
                path=path, dulat_forms={}, entry_meta={}, lemma_map={},
                entry_stems={}, entry_gender={}, udb_words=None, baseline=None,
                input_format="auto", db_checks=False,
            )
            step = YtbMessengerReadingPruner()
            result = step.refine_file(path)
            text = path.read_text(encoding="utf-8")
            self.assertEqual(step.refine_file(path).rows_changed, 0)
            self.assertLessEqual(result.rows_changed, result.rows_processed)
            return original, text, result, issues

    def test_attested_formula_retains_both_finite_alternatives(self):
        for ref in ("KTU 1.5 I:9", "KTU 1.5 II:13", "KTU 1.2 I:19"):
            with self.subTest(ref=ref):
                _, text, result, issues = self.run_case(ref, [PREFIX, PTCP, SUFFIX])
                self.assertNotIn(PTCP, text)
                self.assertIn(PREFIX, text)
                self.assertIn(SUFFIX, text)
                self.assertEqual(result.rows_changed, 1)
                self.assertTrue(any(i.message == YTB_PARTICIPLE_WARNING for i in issues))

    def test_other_attestation_is_unchanged(self):
        original, text, result, issues = self.run_case("KTU 1.5 VI:12", [PREFIX, PTCP])
        self.assertEqual(text, original)
        self.assertEqual(result.rows_changed, 0)
        self.assertFalse(any(i.message == YTB_PARTICIPLE_WARNING for i in issues))

    def test_sole_candidate_is_flagged_but_token_is_not_deleted(self):
        original, text, result, issues = self.run_case("KTU 1.5 I:9", [PTCP])
        self.assertEqual(text, original)
        self.assertEqual(result.rows_changed, 0)
        self.assertTrue(any(i.message == YTB_PARTICIPLE_WARNING for i in issues))

    def test_other_token_cannot_supply_the_finite_candidate(self):
        original, text, result, _ = self.run_case(
            "KTU 1.5 I:9", [PTCP, PREFIX.replace("1\t", "2\t", 1)],
        )
        self.assertEqual(text, original)
        self.assertEqual(result.rows_changed, 0)


if __name__ == "__main__":
    unittest.main()
