#!/usr/bin/env python3
"""Preserve exact changed lines from reviewed-tablet commits as a JSON audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def feedback_hunks(repo: Path, commit: str, tablet: str) -> list[dict]:
    author = subprocess.check_output(
        ["git", "show", "-s", "--format=%an", commit], cwd=repo, text=True,
    ).strip()
    diff = subprocess.check_output(
        ["git", "show", "--format=", "--no-ext-diff", "--unified=0", commit, "--", tablet],
        cwd=repo, text=True,
    )
    records = []
    current = None
    for line in diff.splitlines():
        if line.startswith("@@ "):
            current = {"commit": commit, "author": author, "old_lines": [], "new_lines": []}
            records.append(current)
        elif current is not None and line.startswith("-"):
            current["old_lines"].append(line[1:])
        elif current is not None and line.startswith("+"):
            current["new_lines"].append(line[1:])
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tablet", required=True, help="Repository-relative reviewed TSV path")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("commits", nargs="+")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    records = [
        record
        for commit in args.commits
        for record in feedback_hunks(repo, commit, args.tablet)
    ]
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
