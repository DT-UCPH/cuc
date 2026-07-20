#!/usr/bin/env python3
"""Regenerate tablets, refresh lint, and recalculate reviewed-score deltas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from full_regeneration import FullRegenerationConfig, FullRegenerationRunner  # noqa: E402
from project_paths import get_project_paths  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    paths = get_project_paths(REPO_ROOT)
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate parsed tablets, refresh lint reports, and recalculate "
            "reviewed morphology scores plus before/after deltas."
        )
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
        "--reports-dir",
        default=str(paths.default_reports_dir()),
        help="Directory for lint/scoring reports",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Optional source file basenames (e.g. 'KTU 1.5.tsv')",
    )
    parser.add_argument(
        "--source-glob",
        default="KTU *.tsv",
        help="Glob for source tablet basenames",
    )
    parser.add_argument(
        "--skip-source-refresh",
        action="store_true",
        help="Do not refresh generated Text-Fabric source TSVs before parsing",
    )
    parser.add_argument(
        "--max-step-change-ratio",
        type=float,
        default=0.25,
        help="Safety threshold per step: max changed_rows/processed_rows ratio",
    )
    parser.add_argument(
        "--enforce-step-change-limit",
        action="store_true",
        help="Keep the per-step change-ratio safeguard enabled for this run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show which parsing targets would run",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = get_project_paths(REPO_ROOT)
    reports_dir = Path(args.reports_dir).expanduser().resolve()
    runner = FullRegenerationRunner(paths)
    payload = runner.run(
        FullRegenerationConfig(
            source_dir=Path(args.source_dir).expanduser().resolve(),
            out_dir=Path(args.out_dir).expanduser().resolve(),
            dulat_db=Path(args.dulat_db).expanduser().resolve(),
            udb_db=Path(args.udb_db).expanduser().resolve(),
            reports_dir=reports_dir,
            source_glob=str(args.source_glob),
            include_existing=True,
            allow_large_step_changes=not bool(args.enforce_step_change_limit),
            max_step_change_ratio=float(args.max_step_change_ratio),
            skip_source_refresh=bool(args.skip_source_refresh),
            dry_run=bool(args.dry_run),
            files=tuple(args.files or ()),
        )
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
