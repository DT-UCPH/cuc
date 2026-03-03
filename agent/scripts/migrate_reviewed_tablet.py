#!/usr/bin/env python3
"""Migrate reviewed tablets to current TF-aligned token ids and conventions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from reviewed_migration import ReviewedTabletMigrator  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate a reviewed tablet TSV to current TF-aligned ids and conventions."
    )
    parser.add_argument("reviewed", help="Reviewed TSV file to migrate")
    parser.add_argument("raw", help="Current raw TF-exported TSV file")
    parser.add_argument("auto", help="Current auto-parsed TSV file")
    parser.add_argument(
        "--out",
        default=None,
        help="Output path (defaults to rewriting the reviewed file in place)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reviewed_path = Path(args.reviewed)
    out_path = Path(args.out) if args.out else reviewed_path
    migrator = ReviewedTabletMigrator()
    migrated = migrator.migrate(reviewed_path, Path(args.raw), Path(args.auto))
    out_path.write_text(migrated, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
