"""Tests for the end-to-end full-regeneration runner wrapper."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from full_regeneration.reports import ScoringArtifacts
from full_regeneration.runner import FullRegenerationConfig, FullRegenerationRunner
from project_paths import get_project_paths


class FullRegenerationRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.paths = get_project_paths(Path(__file__).resolve().parents[1])

    def test_dry_run_avoids_source_refresh_and_report_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            pipeline_instance = mock.Mock()
            pipeline_instance.run.return_value = {"targets": ["KTU 1.5.tsv"]}
            config = FullRegenerationConfig(
                source_dir=temp_root / "sources",
                out_dir=temp_root / "out",
                dulat_db=temp_root / "dulat.sqlite",
                udb_db=temp_root / "udb.sqlite",
                reports_dir=temp_root / "reports",
                dry_run=True,
            )

            with (
                mock.patch(
                    "full_regeneration.runner.ensure_generated_cuc_tablet_sources"
                ) as refresh_mock,
                mock.patch(
                    "full_regeneration.runner.TabletParsingPipeline",
                    return_value=pipeline_instance,
                ),
                mock.patch("full_regeneration.runner.LintReportGenerator") as lint_cls,
                mock.patch("full_regeneration.runner.RerunDeltaWriter") as delta_cls,
                mock.patch("full_regeneration.runner.ScoringReportWriter") as score_cls,
            ):
                payload = FullRegenerationRunner(self.paths).run(config)

            refresh_mock.assert_not_called()
            lint_cls.assert_not_called()
            delta_cls.assert_not_called()
            score_cls.assert_not_called()
            pipeline_instance.run.assert_called_once_with(explicit_names=None, dry_run=True)
            self.assertIsNone(payload["lint_delta_report"])
            self.assertIsNone(payload["scoring_report"])

    def test_run_uses_requested_reports_dir_for_lint_and_scoring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_root = Path(tmp_dir)
            reports_dir = (temp_root / "reports").resolve()
            reports_dir.mkdir(parents=True)
            pipeline_instance = mock.Mock()
            pipeline_instance.run.return_value = {"processed_files": 1}
            delta_instance = mock.Mock()
            delta_instance.snapshot_previous_lint_reports.return_value = {
                "total_issues": 9,
                "by_severity": {"ERROR": 4, "WARNING": 3, "INFO": 2},
            }
            delta_instance.write.return_value = {"lint_delta": {"total_issues": -2}}
            scoring_previous = {"summary": {"compared_ids": 2, "macro_f1": 0.5}, "files": []}
            scoring_current = {"summary": {"compared_ids": 3, "macro_f1": 0.6}, "files": []}
            score_instance = mock.Mock()
            score_instance.generate.return_value = ScoringArtifacts(
                previous=scoring_previous,
                current=scoring_current,
            )
            lint_instance = mock.Mock()

            def write_lint_stats() -> int:
                (reports_dir / "lint_stats.json").write_text(
                    json.dumps(
                        {
                            "total_issues": 7,
                            "by_severity": {"ERROR": 3, "WARNING": 3, "INFO": 1},
                            "by_problem_type": [],
                        }
                    ),
                    encoding="utf-8",
                )
                return 1

            lint_instance.run.side_effect = write_lint_stats
            config = FullRegenerationConfig(
                source_dir=temp_root / "sources",
                out_dir=temp_root / "out",
                dulat_db=temp_root / "dulat.sqlite",
                udb_db=temp_root / "udb.sqlite",
                reports_dir=reports_dir,
                skip_source_refresh=True,
            )

            with (
                mock.patch(
                    "full_regeneration.runner.TabletParsingPipeline",
                    return_value=pipeline_instance,
                ),
                mock.patch(
                    "full_regeneration.runner.RerunDeltaWriter",
                    return_value=delta_instance,
                ) as delta_cls,
                mock.patch(
                    "full_regeneration.runner.ScoringReportWriter",
                    return_value=score_instance,
                ) as score_cls,
                mock.patch(
                    "full_regeneration.runner.LintReportGenerator",
                    return_value=lint_instance,
                ) as lint_cls,
            ):
                payload = FullRegenerationRunner(self.paths).run(config)

            delta_cls.assert_called_once_with(reports_dir)
            score_cls.assert_called_once_with(reports_dir)
            lint_cls.assert_called_once_with(
                out_dir=config.out_dir,
                reports_dir=reports_dir,
                dulat_db=config.dulat_db,
                udb_db=config.udb_db,
                linter_path=self.paths.agent_root / "linter" / "lint.py",
            )
            score_instance.generate.assert_called_once_with(
                reviewed_root=self.paths.repo_root / "reviewed",
                auto_root=config.out_dir,
            )
            delta_instance.write.assert_called_once_with(
                lint_before=delta_instance.snapshot_previous_lint_reports.return_value,
                lint_after={
                    "total_issues": 7,
                    "by_severity": {"ERROR": 3, "WARNING": 3, "INFO": 1},
                    "by_problem_type": [],
                },
                scoring_before=scoring_previous,
                scoring_after=scoring_current,
            )
            self.assertEqual(payload["lint_exit_code"], 1)
            self.assertEqual(
                payload["lint_delta_report"],
                str(reports_dir / "rerun_delta_summary.md"),
            )
            self.assertEqual(
                payload["scoring_report"],
                str(reports_dir / "reviewed_morphology_report.md"),
            )


if __name__ == "__main__":
    unittest.main()
