"""Tests for combined full-regeneration scoring/lint report helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from full_regeneration.reports import RerunDeltaWriter, ScoringReportWriter


class FullRegenerationReportsTest(unittest.TestCase):
    def test_rerun_delta_writer_builds_lint_and_scoring_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            reports_dir = Path(tmp_dir)
            writer = RerunDeltaWriter(reports_dir)
            payload = writer.write(
                lint_before={
                    "total_issues": 10,
                    "by_severity": {"ERROR": 4, "WARNING": 3, "INFO": 3},
                    "by_problem_type": [
                        {"severity": "ERROR", "problem_type": "A", "count": 3},
                        {"severity": "WARNING", "problem_type": "B", "count": 2},
                    ],
                },
                lint_after={
                    "total_issues": 7,
                    "by_severity": {"ERROR": 2, "WARNING": 4, "INFO": 1},
                    "by_problem_type": [
                        {"severity": "ERROR", "problem_type": "A", "count": 1},
                        {"severity": "WARNING", "problem_type": "B", "count": 4},
                    ],
                },
                scoring_before={
                    "summary": {
                        "compared_ids": 100,
                        "exact_set_accuracy": 0.5,
                        "macro_f1": 0.6,
                        "micro_f1": 0.7,
                        "gold_coverage": 0.8,
                        "macro_precision": 0.4,
                        "macro_recall": 0.5,
                        "micro_precision": 0.6,
                        "micro_recall": 0.7,
                        "mean_extra_options": 0.2,
                        "mean_missing_options": 0.1,
                    },
                    "files": [
                        {
                            "label": "KTU 1.3.tsv",
                            "summary": {
                                "compared_ids": 50,
                                "exact_set_accuracy": 0.5,
                                "macro_f1": 0.6,
                                "micro_f1": 0.7,
                                "gold_coverage": 0.8,
                            },
                        }
                    ],
                },
                scoring_after={
                    "summary": {
                        "compared_ids": 101,
                        "exact_set_accuracy": 0.55,
                        "macro_f1": 0.61,
                        "micro_f1": 0.71,
                        "gold_coverage": 0.82,
                        "macro_precision": 0.42,
                        "macro_recall": 0.51,
                        "micro_precision": 0.63,
                        "micro_recall": 0.72,
                        "mean_extra_options": 0.19,
                        "mean_missing_options": 0.08,
                    },
                    "files": [
                        {
                            "label": "KTU 1.3.tsv",
                            "summary": {
                                "compared_ids": 51,
                                "exact_set_accuracy": 0.52,
                                "macro_f1": 0.63,
                                "micro_f1": 0.72,
                                "gold_coverage": 0.81,
                            },
                        }
                    ],
                },
            )

            self.assertEqual(payload["lint_delta"]["total_issues"], -3)
            self.assertEqual(payload["lint_delta"]["by_severity"]["ERROR"], -2)
            self.assertEqual(payload["largest_problem_deltas"][0]["problem_type"], "A")
            self.assertAlmostEqual(payload["scoring_delta"]["macro_f1"], 0.01)
            self.assertEqual(payload["per_file_scoring_delta"]["KTU 1.3.tsv"]["compared_ids"], 1)
            self.assertTrue((reports_dir / "rerun_delta_summary.md").exists())
            self.assertTrue((reports_dir / "rerun_delta_summary.json").exists())

    def test_scoring_report_writer_writes_previous_current_and_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            reports_dir = Path(tmp_dir)
            previous_payload = {
                "summary": {
                    "compared_ids": 1,
                    "reviewed_option_count": 1,
                    "auto_option_count": 1,
                    "true_positive_option_count": 1,
                    "exact_set_accuracy": 1.0,
                    "macro_precision": 1.0,
                    "macro_recall": 1.0,
                    "macro_f1": 1.0,
                    "macro_jaccard": 1.0,
                    "micro_precision": 1.0,
                    "micro_recall": 1.0,
                    "micro_f1": 1.0,
                    "gold_coverage": 1.0,
                    "mean_extra_options": 0.0,
                    "mean_missing_options": 0.0,
                    "mean_option_count_error": 0.0,
                },
                "files": [],
            }
            (reports_dir / "reviewed_morphology_report.json").write_text(
                json.dumps(previous_payload),
                encoding="utf-8",
            )

            repo_root = reports_dir / "repo"
            reviewed_dir = repo_root / "reviewed"
            auto_dir = repo_root / "auto"
            reviewed_dir.mkdir(parents=True)
            auto_dir.mkdir(parents=True)
            reviewed_content = (
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.test I:1\t\t\t\t\t\t\n"
                "1\tytn\t!y!(ytn[\t/y-t-n/\tvb\tto give\t\n"
            )
            auto_content = (
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.test I:1\t\t\t\t\t\t\n"
                "1\tytn\t!y!(ytn[\t/y-t-n/\tvb\tto give\t\n"
            )
            (reviewed_dir / "KTU 1.test.tsv").write_text(reviewed_content, encoding="utf-8")
            (auto_dir / "KTU 1.test.tsv").write_text(auto_content, encoding="utf-8")

            writer = ScoringReportWriter(reports_dir)
            artifacts = writer.generate(reviewed_root=reviewed_dir, auto_root=auto_dir)

            self.assertIsNotNone(artifacts.previous)
            self.assertTrue((reports_dir / "reviewed_morphology_report.previous.json").exists())
            self.assertTrue((reports_dir / "reviewed_morphology_report.current.json").exists())
            self.assertTrue((reports_dir / "reviewed_morphology_report.md").exists())
            delta_text = (reports_dir / "reviewed_morphology_report_delta.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("KTU 1.test.tsv", delta_text)
            self.assertEqual(artifacts.current["summary"]["compared_ids"], 1)


if __name__ == "__main__":
    unittest.main()
