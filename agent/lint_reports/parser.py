"""Parsing utilities for morphology linter output."""

import re
from collections import Counter
from typing import Dict, List, Tuple

from lint_reports.constants import MESSAGE_PREFIXES, normalize_message
from lint_reports.models import LintIssue, LintStats, ProblemTypeCount


class LintOutputParser:
    """Parses plain-text output from linter/lint.py."""

    _line_re = re.compile(r"^(ERROR|WARNING|INFO)\s+(.+?):(\d+)\s+(\S+)\s+(.*)$")
    _total_re = re.compile(r"^Total issues:\s+(\d+)\s*$")

    def parse(self, lint_output: str, files_checked: int) -> LintStats:
        by_level: Counter = Counter()
        by_type: Counter = Counter()
        issues: List[LintIssue] = []
        fallback_parsed = 0
        total_issues = None

        for raw in lint_output.splitlines():
            line_match = self._line_re.match(raw)
            if line_match:
                level = line_match.group(1)
                filename = line_match.group(2)
                line_no = int(line_match.group(3))
                line_id = line_match.group(4)
                rest = line_match.group(5)
                message, used_fallback = self._extract_message(rest)
                if used_fallback:
                    fallback_parsed += 1
                normalized_message = normalize_message(message)

                by_level[level] += 1
                by_type[(level, normalized_message)] += 1
                issues.append(
                    LintIssue(
                        level=level,
                        file=filename,
                        line=line_no,
                        line_id=line_id,
                        surface="",
                        message=normalized_message,
                    )
                )
                continue

            total_match = self._total_re.match(raw)
            if total_match:
                total_issues = int(total_match.group(1))

        if total_issues is None:
            total_issues = sum(by_level.values())

        problem_types = [
            ProblemTypeCount(severity=severity, problem_type=problem_type, count=count)
            for (severity, problem_type), count in sorted(
                by_type.items(), key=lambda item: (-item[1], item[0][0], item[0][1])
            )
        ]

        return LintStats(
            files_checked=files_checked,
            total_issues=total_issues,
            fallback_parsed=fallback_parsed,
            by_severity={
                "ERROR": int(by_level.get("ERROR", 0)),
                "WARNING": int(by_level.get("WARNING", 0)),
                "INFO": int(by_level.get("INFO", 0)),
            },
            by_problem_type=problem_types,
            issues=issues,
        )

    def _extract_message(self, rest: str) -> Tuple[str, bool]:
        for prefix in MESSAGE_PREFIXES:
            idx = rest.find(prefix)
            if idx != -1:
                return rest[idx:].strip(), False
        return rest.strip(), True


def build_summary_markdown(stats: LintStats) -> str:
    """Build markdown summary for the current lint run."""
    lines: List[str] = []
    lines.append("## Morphology Lint Summary")
    lines.append("")
    lines.append("- Files checked: `%s`" % stats.files_checked)
    lines.append("- Total issues: `%s`" % stats.total_issues)
    lines.append("- Fallback-parsed issue lines: `%s`" % stats.fallback_parsed)
    lines.append("")

    lines.append("### By Severity")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---:|")
    for level in ("ERROR", "WARNING", "INFO"):
        lines.append("| %s | %d |" % (level, stats.by_severity.get(level, 0)))
    lines.append("")

    lines.append("### By Problem Type")
    lines.append("")
    lines.append("| Severity | Problem Type | Count |")
    lines.append("|---|---|---:|")
    for row in stats.by_problem_type:
        safe_msg = row.problem_type.replace("|", "\\|")
        lines.append("| %s | %s | %d |" % (row.severity, safe_msg, row.count))
    lines.append("")
    return "\n".join(lines)


def stats_to_json_dict(stats: LintStats, generated_at_utc: str) -> Dict[str, object]:
    """Convert stats to JSON-serializable payload."""
    return {
        "generated_at_utc": generated_at_utc,
        "files_checked": stats.files_checked,
        "total_issues": stats.total_issues,
        "fallback_parsed": stats.fallback_parsed,
        "by_severity": dict(stats.by_severity),
        "by_problem_type": [
            {
                "severity": item.severity,
                "problem_type": item.problem_type,
                "count": item.count,
            }
            for item in stats.by_problem_type
        ],
    }
