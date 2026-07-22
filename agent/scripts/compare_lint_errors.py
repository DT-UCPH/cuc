#!/usr/bin/env python3
"""Report ERROR occurrences introduced between two morphology lint runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lint_reports.regression import find_new_issues, read_lint_issues  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="linter output for the HEAD version")
    parser.add_argument("candidate", type=Path, help="linter output for the staged version")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    new_issues = find_new_issues(read_lint_issues(args.baseline), read_lint_issues(args.candidate))
    for issue in new_issues:
        print(issue.rendered)
    return 1 if new_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
