#!/usr/bin/env python3
"""CLI entrypoint for the tablet parsing pipeline."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse KTU tablets into out/*.tsv and refresh reports."
    )
    parser.add_argument(
        "--source-dir",
        default="cuc_tablets_tsv",
        help="Directory with raw source tablets",
    )
    parser.add_argument(
        "--out-dir",
        default="out",
        help="Directory for structured parsed tablets",
    )
    parser.add_argument(
        "--dulat-db",
        default="sources/dulat_cache.sqlite",
        help="Path to DULAT sqlite cache",
    )
    parser.add_argument(
        "--udb-db",
        default="sources/udb_cache.sqlite",
        help="Path to UDB sqlite cache",
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Reprocess files already present in out/",
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
    return parser


def main() -> int:
    from pipeline.tablet_parsing import PipelineConfig, TabletParsingPipeline

    args = build_parser().parse_args()

    config = PipelineConfig(
        source_dir=Path(args.source_dir),
        out_dir=Path(args.out_dir),
        dulat_db=Path(args.dulat_db),
        udb_db=Path(args.udb_db),
        include_existing=bool(args.include_existing),
        max_step_change_ratio=float(args.max_step_change_ratio),
        allow_large_step_changes=bool(args.allow_large_step_changes),
    )
    pipeline = TabletParsingPipeline(config=config)
    summary = pipeline.run(explicit_names=args.files, dry_run=bool(args.dry_run))

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
