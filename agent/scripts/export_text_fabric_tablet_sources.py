#!/usr/bin/env python3
"""Export canonical raw tablet TSV files from the latest Text-Fabric dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from project_paths import get_project_paths  # noqa: E402
from text_fabric import TextFabricTabletSourceExporter  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    paths = get_project_paths(REPO_ROOT)
    parser = argparse.ArgumentParser(
        description="Export raw cuc_tablets_tsv files from Text-Fabric data."
    )
    parser.add_argument(
        "--tf-version",
        default=None,
        help="Specific Text-Fabric version to export (defaults to latest available).",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help=(
            "Output directory for generated raw TSV files "
            "(defaults to agent/generated_sources/cuc_tablets_tsv/<version>)."
        ),
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Keep existing TSV files in the output directory before exporting.",
    )
    parser.add_argument(
        "--tf-root",
        default=str(paths.tf_root_dir),
        help="Text-Fabric root directory (default: ../tf).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    paths = get_project_paths(REPO_ROOT)
    exporter = TextFabricTabletSourceExporter(
        repo_root=paths.repo_root,
        tf_root=Path(args.tf_root),
        generated_root=paths.generated_sources_dir,
    )
    summary = exporter.export(
        version=args.tf_version,
        out_dir=Path(args.out_dir).expanduser().resolve() if args.out_dir else None,
        clean=not args.no_clean,
    )
    print(
        json.dumps(
            {
                "tf_version": summary.tf_version,
                "output_dir": str(summary.output_dir),
                "file_count": summary.file_count,
                "token_count": summary.token_count,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
