"""Orchestrate full-tablet regeneration plus lint/scoring delta reporting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from full_regeneration.reports import RerunDeltaWriter, ScoringReportWriter
from lint_reports.generator import LintReportGenerator
from pipeline.tablet_parsing import PipelineConfig, TabletParsingPipeline
from project_paths import ProjectPaths
from text_fabric import ensure_generated_cuc_tablet_sources


@dataclass(frozen=True)
class FullRegenerationConfig:
    """Config for one full regeneration run."""

    source_dir: Path
    out_dir: Path
    dulat_db: Path
    udb_db: Path
    reports_dir: Path
    source_glob: str = "KTU *.tsv"
    include_existing: bool = True
    allow_large_step_changes: bool = True
    max_step_change_ratio: float = 0.25
    skip_source_refresh: bool = False
    dry_run: bool = False
    files: tuple[str, ...] = ()


class FullRegenerationRunner:
    """Run the end-to-end refresh workflow and materialize delta reports."""

    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths

    def run(self, config: FullRegenerationConfig) -> dict[str, Any]:
        source_dir = config.source_dir.expanduser().resolve()
        reports_dir = config.reports_dir.expanduser().resolve()
        export_summary = None
        if not config.skip_source_refresh and not config.dry_run:
            export_summary = ensure_generated_cuc_tablet_sources(self.paths, source_dir)
            if export_summary is not None:
                source_dir = export_summary.output_dir

        pipeline = TabletParsingPipeline(
            PipelineConfig(
                source_dir=source_dir,
                out_dir=config.out_dir,
                dulat_db=config.dulat_db,
                udb_db=config.udb_db,
                include_existing=config.include_existing,
                source_glob=config.source_glob,
                max_step_change_ratio=config.max_step_change_ratio,
                allow_large_step_changes=config.allow_large_step_changes,
            )
        )
        pipeline_summary = pipeline.run(
            explicit_names=list(config.files) or None,
            dry_run=config.dry_run,
        )
        pipeline_summary["source_dir"] = str(source_dir)
        if export_summary is not None:
            pipeline_summary["source_export"] = {
                "tf_version": export_summary.tf_version,
                "output_dir": str(export_summary.output_dir),
                "file_count": export_summary.file_count,
                "token_count": export_summary.token_count,
            }

        if config.dry_run:
            return {
                "pipeline": pipeline_summary,
                "lint_delta_report": None,
                "scoring_report": None,
            }

        delta_writer = RerunDeltaWriter(reports_dir)
        score_writer = ScoringReportWriter(reports_dir)
        lint_before = delta_writer.snapshot_previous_lint_reports()
        lint_generator = LintReportGenerator(
            out_dir=config.out_dir,
            reports_dir=reports_dir,
            dulat_db=config.dulat_db,
            udb_db=config.udb_db,
            linter_path=self.paths.agent_root / "linter" / "lint.py",
        )
        lint_exit_code = lint_generator.run()
        lint_after = self._load_json(reports_dir / "lint_stats.json")
        scoring = score_writer.generate(
            reviewed_root=self.paths.repo_root / "reviewed",
            auto_root=config.out_dir,
        )
        delta_payload = delta_writer.write(
            lint_before=lint_before,
            lint_after=lint_after,
            scoring_before=scoring.previous,
            scoring_after=scoring.current,
        )

        return {
            "pipeline": pipeline_summary,
            "lint_exit_code": lint_exit_code,
            "lint_delta_report": str(reports_dir / "rerun_delta_summary.md"),
            "scoring_report": str(reports_dir / "reviewed_morphology_report.md"),
            "delta": delta_payload,
        }

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        import json

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
