#!/usr/bin/env python3
"""CLI entrypoint for the tablet parsing pipeline."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from project_paths import get_project_paths  # noqa: E402
from text_fabric import ensure_generated_cuc_tablet_sources  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    paths = get_project_paths(REPO_ROOT)
    parser = argparse.ArgumentParser(
        description="Parse KTU tablets into structured TSV output and refresh reports."
    )
    parser.add_argument(
        "--source-dir",
        default=str(paths.default_source_dir()),
        help="Directory with raw source tablets",
    )
    parser.add_argument(
        "--out-dir",
        default=str(paths.default_output_dir()),
        help="Directory for structured parsed tablets",
    )
    parser.add_argument(
        "--dulat-db",
        default=str(paths.default_dulat_db()),
        help="Path to DULAT sqlite cache",
    )
    parser.add_argument(
        "--udb-db",
        default=str(paths.default_udb_db()),
        help="Path to UDB sqlite cache",
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Reprocess files already present in the output directory",
    )
    parser.add_argument(
        "--source-glob",
        default="KTU *.tsv",
        help="Glob for source tablet basenames (default: 'KTU *.tsv')",
    )
    parser.add_argument(
        "--max-step-change-ratio",
        type=float,
        default=0.25,
        help="Safety threshold per step: max changed_rows/processed_rows ratio (default: 0.25)",
    )
    parser.add_argument(
        "--allow-large-step-changes",
        action="store_true",
        help="Disable per-step change-ratio safeguard",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit source file basenames (e.g., 'KTU 1.181.tsv')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show selected targets without writing changes",
    )
    parser.add_argument(
        "--skip-source-refresh",
        action="store_true",
        help="Do not refresh generated Text-Fabric raw sources before parsing",
    )
    return parser


def main() -> int:
    from pipeline.tablet_parsing import PipelineConfig, TabletParsingPipeline

    args = build_parser().parse_args()
    paths = get_project_paths(REPO_ROOT)
    source_dir = Path(args.source_dir).expanduser().resolve()
    export_summary = None
    if not args.skip_source_refresh:
        export_summary = ensure_generated_cuc_tablet_sources(paths, source_dir)
        if export_summary is not None:
            source_dir = export_summary.output_dir

    config = PipelineConfig(
        source_dir=source_dir,
        out_dir=Path(args.out_dir),
        dulat_db=Path(args.dulat_db),
        udb_db=Path(args.udb_db),
        include_existing=bool(args.include_existing),
        source_glob=str(args.source_glob),
        max_step_change_ratio=float(args.max_step_change_ratio),
        allow_large_step_changes=bool(args.allow_large_step_changes),
    )
    pipeline = TabletParsingPipeline(config=config)
    summary = pipeline.run(explicit_names=args.files, dry_run=bool(args.dry_run))
    summary["source_dir"] = str(source_dir)
    if export_summary is not None:
        summary["source_export"] = {
            "tf_version": export_summary.tf_version,
            "output_dir": str(export_summary.output_dir),
            "file_count": export_summary.file_count,
            "token_count": export_summary.token_count,
        }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
