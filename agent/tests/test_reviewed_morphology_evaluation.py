from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reviewed_evaluation.loader import EvaluationTargetResolver, MorphologyTsvLoader
from reviewed_evaluation.scorer import MorphologyAgreementScorer


class MorphologyTsvLoaderTest(unittest.TestCase):
    def test_loads_fixture_and_groups_unique_analyses_by_id(self) -> None:
        dataset = MorphologyTsvLoader().load(Path("tests/fixtures/reviewed_ktu_1_5_cases.tsv"))

        self.assertEqual(dataset.token_count, 11)
        token = dataset.tokens_by_id["139782"]
        self.assertEqual(token.surface, "tṯkḥ")
        self.assertEqual(
            token.analyses,
            frozenset({"!t!ṯkḥ[:w", "!t!ṯkḥ["}),
        )

    def test_recovers_collapsed_surface_and_analysis_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "reviewed.txt"
            path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "139808\tyṯb yṯb[\t/y-ṯ-b/\tvb G suffc. 3 m. sg.\tto sit down\t\t\n"
                "139808\tyṯb\t!y!(yṯb[\t/y-ṯ-b/\tvb G prefc. 3 m. sg.\tto sit down\t\n",
                encoding="utf-8",
            )

            dataset = MorphologyTsvLoader().load(path)

        token = dataset.tokens_by_id["139808"]
        self.assertEqual(token.surface, "yṯb")
        self.assertEqual(token.analyses, frozenset({"yṯb[", "!y!(yṯb["}))


class EvaluationTargetResolverTest(unittest.TestCase):
    def test_matches_reviewed_and_auto_files_by_basename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed_dir = root / "reviewed"
            auto_dir = root / "auto"
            reviewed_dir.mkdir()
            auto_dir.mkdir()
            (reviewed_dir / "KTU 1.1.tsv").write_text("", encoding="utf-8")
            (reviewed_dir / "KTU 1.2.tsv").write_text("", encoding="utf-8")
            (auto_dir / "KTU 1.1.tsv").write_text("", encoding="utf-8")

            pairs = EvaluationTargetResolver().resolve(reviewed_dir, auto_dir)

            self.assertEqual([pair.label for pair in pairs], ["KTU 1.1.tsv", "KTU 1.2.tsv"])
            self.assertIsNotNone(pairs[0].auto_path)
            self.assertIsNone(pairs[1].auto_path)

    def test_matches_reviewed_txt_files_to_auto_tsv_by_stem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed_dir = root / "reviewed"
            auto_dir = root / "auto"
            reviewed_dir.mkdir()
            auto_dir.mkdir()
            (reviewed_dir / "KTU 1.3.tsv").write_text("", encoding="utf-8")
            (reviewed_dir / "KTU 1.5.txt").write_text("", encoding="utf-8")
            (auto_dir / "KTU 1.3.tsv").write_text("", encoding="utf-8")
            (auto_dir / "KTU 1.5.tsv").write_text("", encoding="utf-8")

            pairs = EvaluationTargetResolver().resolve(reviewed_dir, auto_dir)

            self.assertEqual(
                [pair.label for pair in pairs],
                ["KTU 1.3.tsv", "KTU 1.5.txt"],
            )
            self.assertEqual(pairs[0].auto_path, auto_dir / "KTU 1.3.tsv")
            self.assertEqual(pairs[1].auto_path, auto_dir / "KTU 1.5.tsv")


class MorphologyAgreementScorerTest(unittest.TestCase):
    maxDiff = None

    def test_scores_unordered_option_sets_and_missing_auto_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed_path = root / "reviewed.tsv"
            auto_path = root / "auto.tsv"
            reviewed_path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.1 I:1\t\t\t\t\t\t\n"
                "1\tab\ta1\t\t\t\t\n"
                "1\tab\ta2\t\t\t\t\n"
                "2\tcd\tb1\t\t\t\t\n"
                "3\tef\tc1\t\t\t\t\n"
                "3\tef\tc2\t\t\t\t\n",
                encoding="utf-8",
            )
            auto_path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.1 I:1\t\t\t\t\t\t\n"
                "1\tab\ta2\t\t\t\t\n"
                "1\tab\ta1\t\t\t\t\n"
                "1\tab\ta1\t\t\t\tduplicate\n"
                "2\tcd\tb1\t\t\t\t\n"
                "2\tcd\tb2\t\t\t\t\n"
                "4\tgh\td1\t\t\t\t\n",
                encoding="utf-8",
            )

            loader = MorphologyTsvLoader()
            scorer = MorphologyAgreementScorer()
            result = scorer.score_file_pair(
                label="KTU 1.1.tsv",
                reviewed=loader.load(reviewed_path),
                auto=loader.load(auto_path),
            )

        self.assertEqual(result.reviewed_token_count, 3)
        self.assertEqual(result.auto_token_count, 3)
        self.assertEqual(result.missing_auto_ids, ("3",))
        self.assertEqual(result.extra_auto_ids, ("4",))

        summary = result.summary
        self.assertEqual(summary.compared_ids, 3)
        self.assertAlmostEqual(summary.exact_set_accuracy, 1 / 3)
        self.assertAlmostEqual(summary.macro_precision, 0.5)
        self.assertAlmostEqual(summary.macro_recall, 2 / 3)
        self.assertAlmostEqual(summary.macro_f1, 5 / 9)
        self.assertAlmostEqual(summary.macro_jaccard, 0.5)
        self.assertAlmostEqual(summary.micro_precision, 0.75)
        self.assertAlmostEqual(summary.micro_recall, 0.6)
        self.assertAlmostEqual(summary.micro_f1, 2 / 3)
        self.assertAlmostEqual(summary.gold_coverage, 2 / 3)
        self.assertAlmostEqual(summary.mean_extra_options, 1 / 3)
        self.assertAlmostEqual(summary.mean_missing_options, 2 / 3)
        self.assertAlmostEqual(summary.mean_option_count_error, 1.0)

        self.assertIsNotNone(result.unambiguous_summary)
        self.assertIsNotNone(result.ambiguous_summary)
        self.assertEqual(result.unambiguous_summary.compared_ids, 1)
        self.assertEqual(result.ambiguous_summary.compared_ids, 2)
        self.assertAlmostEqual(result.unambiguous_summary.exact_set_accuracy, 0.0)
        self.assertAlmostEqual(result.ambiguous_summary.exact_set_accuracy, 0.5)

        mismatch = next(item for item in result.per_id if item.token_id == "2")
        self.assertEqual(mismatch.reviewed_analyses, ("b1",))
        self.assertEqual(mismatch.auto_analyses, ("b1", "b2"))
        self.assertEqual(mismatch.extra_analyses, ("b2",))
        self.assertEqual(mismatch.missing_analyses, ())
        self.assertFalse(mismatch.exact_set_match)

    def test_result_serializes_to_json_ready_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed_path = root / "reviewed.tsv"
            reviewed_path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "1\tab\ta1\t\t\t\t\n",
                encoding="utf-8",
            )

            loader = MorphologyTsvLoader()
            scorer = MorphologyAgreementScorer()
            result = scorer.score_file_pair(
                label="reviewed.tsv",
                reviewed=loader.load(reviewed_path),
                auto=loader.empty("auto.tsv"),
            )

        payload = result.to_dict()
        encoded = json.dumps(payload, ensure_ascii=False)

        self.assertIn('"label": "reviewed.tsv"', encoded)
        self.assertIn('"missing_auto_ids": ["1"]', encoded)
        self.assertIn('"micro_f1"', encoded)


if __name__ == "__main__":
    unittest.main()
