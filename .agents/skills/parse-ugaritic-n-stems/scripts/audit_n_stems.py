#!/usr/bin/env python3
"""Audit explicit N-stem markers in labeled Ugaritic TSV files."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

N_POS_RE = re.compile(r"\bvb\.?\s+N\b", re.IGNORECASE)
PREFC_RE = re.compile(r"\bprefc\.", re.IGNORECASE)
SUFFC_RE = re.compile(r"\bsuffc\.", re.IGNORECASE)
PREFORMATIVE_RE = re.compile(r"^(?:![ytan](?:=+)?!|!\(ʔ&[aiu]!)", re.IGNORECASE)
ROOT_INITIAL_N_RE = re.compile(r"^/n-")


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
                dulat = variant(dulat_values, index)
                if not N_POS_RE.search(pos):
                    continue
                prefix = f"{path}:{line_no} {line_id} {surface}"
                if "](n]" in analysis:
                    issues.append(f"{prefix}\tdeprecated-marker-order\t{analysis}")
                if SUFFC_RE.search(pos):
                    if "]n]" not in analysis:
                        issues.append(f"{prefix}\tmissing-suffix-N-marker\t{analysis}")
                    if ROOT_INITIAL_N_RE.match(dulat) and not analysis.startswith("]n](n"):
                        issues.append(f"{prefix}\troot-initial-n-not-separated\t{analysis}")
                elif PREFC_RE.search(pos):
                    match = PREFORMATIVE_RE.match(analysis)
                    if match is not None:
                        tail = analysis[match.end() :]
                        if not tail.startswith(("(]n]", "]n]")):
                            issues.append(f"{prefix}\tmissing-prefixed-N-marker\t{analysis}")
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
