#!/usr/bin/env python3
"""Check Ugaritic analysis-to-surface reconstruction with repository semantics."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def find_repo_root() -> Path:
    starts = [Path.cwd(), *Path(__file__).resolve().parents]
    for start in starts:
        candidate = start.resolve()
        if (candidate / "agent/pipeline/steps/analysis_utils.py").is_file():
            return candidate
    raise RuntimeError("cannot find repository root containing agent/pipeline/steps/analysis_utils.py")


REPO_ROOT = find_repo_root()
sys.path.insert(0, str(REPO_ROOT / "agent"))

from pipeline.steps.analysis_utils import (  # noqa: E402
    analysis_matches_surface,
    reconstruct_surface_from_analysis,
)


def iter_tsv_paths(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.tsv")))
        elif path.suffix == ".tsv":
            paths.append(path)
    return paths


def split_variants(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def check_pair(surface: str, analysis: str) -> tuple[bool, str]:
    reconstructed = reconstruct_surface_from_analysis(analysis)
    return analysis_matches_surface(surface, analysis), reconstructed


def audit_file(path: Path, *, show_ok: bool) -> tuple[list[str], int, int]:
    messages: list[str] = []
    checked = 0
    skipped = 0
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"id", "surface form", "morphological parsing"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return [f"MISMATCH {path}: unsupported TSV header"], checked, skipped
        for line_no, row in enumerate(reader, 2):
            line_id = (row.get("id") or "").strip()
            if not line_id or line_id.startswith("#"):
                continue
            surface = (row.get("surface form") or "").strip()
            comment = (row.get("comments") or "").upper()
            analyses = split_variants(row.get("morphological parsing") or "")
            if "MERGE WITH THE " in comment:
                skipped += sum(1 for analysis in analyses if analysis and analysis != "?")
                messages.append(f"SKIP-MERGE {path}:{line_no} {line_id} {surface}")
                continue
            for analysis in analyses:
                if not analysis or analysis == "?":
                    continue
                checked += 1
                ok, reconstructed = check_pair(surface, analysis)
                if not ok:
                    messages.append(
                        f"MISMATCH {path}:{line_no} {line_id} {surface}\t{analysis}\t-> {reconstructed}"
                    )
                elif show_ok:
                    messages.append(f"OK {path}:{line_no} {line_id} {surface}\t{analysis}")
    return messages, checked, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="TSV files or directories containing TSVs")
    parser.add_argument(
        "--pair",
        nargs=2,
        action="append",
        metavar=("SURFACE", "ANALYSIS"),
        default=[],
        help="check one surface-analysis pair; may be repeated",
    )
    parser.add_argument("--show-ok", action="store_true", help="print successful TSV rows")
    args = parser.parse_args()

    mismatch_count = 0
    checked = 0
    skipped = 0
    for surface, analysis in args.pair:
        ok, reconstructed = check_pair(surface, analysis)
        checked += 1
        status = "OK" if ok else "MISMATCH"
        print(f"{status} {surface}\t{analysis}\t-> {reconstructed}")
        mismatch_count += int(not ok)

    paths = iter_tsv_paths(args.paths)
    if args.paths and not paths:
        parser.error("no TSV files found")
    for path in paths:
        messages, file_checked, file_skipped = audit_file(path, show_ok=args.show_ok)
        for message in messages:
            print(message)
            mismatch_count += int(message.startswith("MISMATCH"))
        checked += file_checked
        skipped += file_skipped

    if not args.pair and not paths:
        parser.error("provide --pair or at least one TSV path")
    print(f"Checked {checked} analysis variant(s); {mismatch_count} mismatch(es); {skipped} merge exception(s).")
    return 1 if mismatch_count else 0


if __name__ == "__main__":
    sys.exit(main())
