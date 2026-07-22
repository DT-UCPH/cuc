#!/usr/bin/env python3
"""Audit explicit Gt-stem markers in labeled Ugaritic TSV files."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

FIRM_GT_POS_RE = re.compile(r"^\s*vb\.?\s+Gt(?![?/\w])", re.IGNORECASE)
ROOT_RE = re.compile(r"^/(?P<first>[^-/()])(?:[-(])")
REVERSED_ELIDED_FIRST_RE = re.compile(r"]t]\((?P<first>[nh])", re.IGNORECASE)


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


def variant(values: list[str], index: int) -> str:
    if index < len(values):
        return values[index]
    if len(values) == 1:
        return values[0]
    return ""


def audit_file(path: Path, *, selected_ids: set[str]) -> list[str]:
    issues: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"id", "surface form", "morphological parsing", "DULAT", "POS"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return [f"{path}: unsupported TSV header"]
        for line_no, row in enumerate(reader, 2):
            line_id = (row.get("id") or "").strip()
            if not line_id or line_id.startswith("#"):
                continue
            if selected_ids and line_id not in selected_ids:
                continue
            surface = (row.get("surface form") or "").strip()
            analyses = split_variants(row.get("morphological parsing") or "")
            pos_values = split_variants(row.get("POS") or "")
            dulat_values = split_variants(row.get("DULAT") or "")
            for index, analysis in enumerate(analyses):
                pos = variant(pos_values, index)
                if not FIRM_GT_POS_RE.search(pos):
                    continue
                dulat = variant(dulat_values, index)
                prefix = f"{path}:{line_no} {line_id} {surface}"
                if "]t]" not in analysis:
                    issues.append(f"{prefix}\tmissing-Gt-marker\t{analysis}")
                    continue
                reversed_match = REVERSED_ELIDED_FIRST_RE.search(analysis)
                root_match = ROOT_RE.match(dulat)
                if (
                    reversed_match is not None
                    and root_match is not None
                    and reversed_match.group("first") == root_match.group("first")
                ):
                    issues.append(
                        f"{prefix}\tGt-marker-before-elided-first-radical\t{analysis}"
                    )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="TSV files or directories containing TSVs")
    parser.add_argument("--id", action="append", default=[], help="limit the audit to one token ID")
    args = parser.parse_args()

    paths = iter_tsv_paths(args.paths)
    if not paths:
        parser.error("no TSV files found")
    selected_ids = set(args.id)
    issues = [
        issue for path in paths for issue in audit_file(path, selected_ids=selected_ids)
    ]
    for issue in issues:
        print(issue)
    print(f"Audited {len(paths)} file(s); found {len(issues)} issue(s).")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
