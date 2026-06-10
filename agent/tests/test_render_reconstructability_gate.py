"""End-of-pipeline fallback for tokens with no reconstructable analysis.

The gate must run after all repair steps: rendering emits repairable
baselines (il(I)/ for ilm, lqḥ[ for yqḥ), so render-time gating rejected
healthy tokens (regression: ilm, yqḥ, bˤlny, ˤbdk). Only what still cannot
reconstruct at the end of the pipeline (yddll -> dll[:d) becomes '?' with
the DULAT candidates preserved as a comment hint.
"""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.unresolvable_token_fallback import UnresolvableTokenFallback
from scripts.refine_results_mentions import analysis_reconstructs

HEADER = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"


def _run(rows: list[str]) -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "KTU 1.test.tsv"
        body = "".join(r + "\n" for r in rows)
        path.write_text(HEADER + "# KTU 1.103 1\t\t\t\t\t\t\n" + body, encoding="utf-8")
        UnresolvableTokenFallback().refine_file(path)
        return path.read_text(encoding="utf-8")


class AnalysisReconstructsTest(unittest.TestCase):
    def test_repaired_full_pipeline_outputs_reconstruct(self) -> None:
        for surface, analysis in (
            ("ilm", "il(I)/m"),
            ("yqḥ", "!y!(lqḥ["),
            ("bˤlny", "bˤl(II)/+ny"),
            ("ˤbdk", "ˤbd(I)/+k"),
            ("tṯṯb", "!t!](š&ṯ]ṯb["),
        ):
            self.assertTrue(analysis_reconstructs(surface, analysis), (surface, analysis))

    def test_unsound_analyses_do_not_reconstruct(self) -> None:
        self.assertFalse(analysis_reconstructs("yddll", "dll[:d"))
        self.assertFalse(analysis_reconstructs("gh", "ytn["))


class UnresolvableTokenFallbackTest(unittest.TestCase):
    def test_unreconstructable_group_becomes_hint_row(self) -> None:
        result = _run(["1\tyddll\tdll[:d\t/d-l-l/\tvb D prefc.\tto oppress, subdue\t"])
        self.assertIn("\t?\t?\t?\t?\t", result)
        self.assertIn(
            "DULAT candidates (no reconstructable encoding): /d-l-l/ - to oppress", result
        )
        self.assertNotIn("dll[:d", result)

    def test_reconstructable_rows_are_untouched(self) -> None:
        result = _run(
            [
                "1\tilm\til(I)/m\tỉl (I)\tn. m. pl. abs. gen.\tgod\t",
                "2\tˤbdk\tˤbd(I)/+k\tʕbd (I)\tn. m. du. cstr. gen.\tservant\t",
            ]
        )
        self.assertIn("il(I)/m", result)
        self.assertIn("ˤbd(I)/+k", result)
        self.assertNotIn("DULAT candidates", result)

    def test_group_with_one_healthy_variant_is_untouched(self) -> None:
        result = _run(
            [
                "1\tgh\tytn[\t/y-t-n/\tvb\tto give\t",
                "1\tgh\tg/+h\tg\tn. m. sg.\t(loud) voice\t",
            ]
        )
        self.assertNotIn("DULAT candidates", result)

    def test_protected_rows_are_untouched(self) -> None:
        result = _run(
            [
                "1\txxdll\tdll[:d\t/d-l-l/\tvb\tto oppress\t",
                "2\tsbn\tsb(b[ny\t/s-b-b/\tvb\tto go around\tMERGE WITH THE NEXT: sbn+y.",
                "3\ty\tsb(b[ny\t/s-b-b/\tvb\tto go around\tMERGE WITH THE PREVIOUS.",
            ]
        )
        self.assertIn("dll[:d", result)
        self.assertEqual(result.count("sb(b[ny"), 2)


if __name__ == "__main__":
    unittest.main()
