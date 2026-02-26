#!/usr/bin/env python3
"""Parse committed reports and publish compact CI summary."""

import json
import os
from pathlib import Path
from typing import Dict, List

REQUIRED_REPORTS = [
    "lint_stats.json",
    "lint_summary.md",
    "lint_history.json",
    "lint_trends.md",
    "lint_severity_trend.svg",
    "lint_issue_types_trend.svg",
]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _top_problem_types(stats_payload: Dict[str, object], limit: int = 8) -> List[Dict[str, object]]:
    rows = stats_payload.get("by_problem_type") or []
    valid = [row for row in rows if isinstance(row, dict)]
    valid.sort(key=lambda row: (-int(row.get("count", 0) or 0), str(row.get("problem_type", ""))))
    return valid[:limit]


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    reports_dir = repo_root / "reports"

    missing = [name for name in REQUIRED_REPORTS if not (reports_dir / name).exists()]
    if missing:
        print("Missing reports: %s" % ", ".join(missing))
        return 2

    stats_payload = _read_json(reports_dir / "lint_stats.json")
    history = _read_json(reports_dir / "lint_history.json")
    if not isinstance(history, list) or not history:
        print("Invalid or empty reports/lint_history.json")
        return 3

    latest = history[-1]
    previous = history[-2] if len(history) > 1 else None

    total = int(stats_payload.get("total_issues", 0) or 0)
    sev = stats_payload.get("by_severity") or {}

    summary_lines = []
    summary_lines.append("## Morphology Lint (Parsed Reports)")
    summary_lines.append("")
    summary_lines.append("- Files checked: `%s`" % int(stats_payload.get("files_checked", 0) or 0))
    summary_lines.append("- Total issues: `%d`" % total)
    summary_lines.append("- Report timestamp (UTC): `%s`" % (stats_payload.get("generated_at_utc") or ""))
    summary_lines.append("- History points: `%d`" % len(history))
    summary_lines.append("- Latest history git head: `%s`" % (latest.get("git_head") or ""))
    summary_lines.append("")

    summary_lines.append("### By Severity")
    summary_lines.append("")
    summary_lines.append("| Severity | Count |")
    summary_lines.append("|---|---:|")
    for level in ("ERROR", "WARNING", "INFO"):
        summary_lines.append("| %s | %d |" % (level, int(sev.get(level, 0) or 0)))
    summary_lines.append("")

    if previous:
        summary_lines.append("### Delta vs Previous History Point")
        summary_lines.append("")
        summary_lines.append("| Metric | Current | Previous | Delta |")
        summary_lines.append("|---|---:|---:|---:|")
        prev_total = int(previous.get("total_issues", 0) or 0)
        summary_lines.append(
            "| Total issues | %d | %d | %+d |" % (total, prev_total, total - prev_total)
        )
        prev_sev = previous.get("by_severity") or {}
        for level in ("ERROR", "WARNING", "INFO"):
            cur = int(sev.get(level, 0) or 0)
            prev = int(prev_sev.get(level, 0) or 0)
            summary_lines.append("| %s | %d | %d | %+d |" % (level, cur, prev, cur - prev))
        summary_lines.append("")

    summary_lines.append("### Top Problem Types")
    summary_lines.append("")
    summary_lines.append("| Severity | Problem Type | Count |")
    summary_lines.append("|---|---|---:|")
    for row in _top_problem_types(stats_payload):
        problem = str(row.get("problem_type", "")).replace("|", "\\|")
        summary_lines.append(
            "| %s | %s | %d |"
            % (row.get("severity", ""), problem, int(row.get("count", 0) or 0))
        )
    summary_lines.append("")
    summary_lines.append(
        "Plots are committed under `reports/lint_severity_trend.svg` and `reports/lint_issue_types_trend.svg`."
    )

    summary = "\n".join(summary_lines) + "\n"
    print(summary)

    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        with open(step_summary_path, "a", encoding="utf-8") as handle:
            handle.write(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
