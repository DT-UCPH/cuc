import unittest

from pipeline.steps.base import TabletRow
from pipeline.steps.verb_mixed_stem_split import VerbMixedStemSplitFixer


class VerbMixedStemSplitFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = VerbMixedStemSplitFixer()

    def test_splits_g_and_d_prefixed_rows(self) -> None:
        row = TabletRow(
            "1",
            "yšlm",
            "!y!šlm[:d",
            "/š-l-m/",
            "vb G prefc. / vb D prefc.",
            "to be well",
            "",
        )

        result = self.fixer.refine_row(row)

        self.assertEqual(result.analysis, "!y!šlm[; !y!šlm[:d")
        self.assertEqual(result.dulat, "/š-l-m/; /š-l-m/")
        self.assertEqual(result.pos, "vb G prefc.; vb D prefc.")
        self.assertEqual(result.gloss, "to be well; to be well")

    def test_splits_g_n_and_gpass_rows_and_strips_union_markers(self) -> None:
        row = TabletRow(
            "1",
            "ybn",
            "!y!(]n]bn(y[:pass",
            "/b-n-y/",
            "vb G prefc. / vb N prefc. / vb Gpass prefc.",
            "to build",
            "",
        )

        result = self.fixer.refine_row(row)

        self.assertEqual(result.analysis, "!y!bn(y[; !y!(]n]bn(y[; !y!bn(y[:pass")
        self.assertEqual(result.dulat, "/b-n-y/; /b-n-y/; /b-n-y/")
        self.assertEqual(
            result.pos,
            "vb G prefc.; vb N prefc.; vb Gpass prefc.",
        )
        self.assertEqual(result.gloss, "to build; to build; to build")

    def test_pairs_preexpanded_analysis_variants_to_stem_groups(self) -> None:
        row = TabletRow(
            "1",
            "ybnn",
            "!y!(]n]bn(y[:pass+n; !y!(]n]bn(y[+n; !y!bn(y[:pass+n",
            "/b-n-y/; /b-n-y/; /b-n-y/",
            "vb G prefc. / vb N prefc. / vb Gpass prefc.",
            "to build; to build; to build",
            "",
        )

        result = self.fixer.refine_row(row)

        self.assertEqual(result.analysis, "!y!bn(y[+n; !y!(]n]bn(y[+n; !y!bn(y[:pass+n")
        self.assertEqual(
            result.pos,
            "vb G prefc.; vb N prefc.; vb Gpass prefc.",
        )


if __name__ == "__main__":
    unittest.main()
