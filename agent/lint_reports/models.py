"""Data models for lint report generation and parsing."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LintIssue:
    """Single parsed linter issue line."""

    level: str
    file: str
    line: int
    line_id: str
    surface: str
    message: str


@dataclass
class ProblemTypeCount:
    """Aggregated count for one problem category."""

    severity: str
    problem_type: str
    count: int


@dataclass
class LintStats:
    """Aggregated report payload stored in reports/lint_stats.json."""

    files_checked: int
    total_issues: int
    fallback_parsed: int
    by_severity: Dict[str, int]
    by_problem_type: List[ProblemTypeCount]
    issues: List[LintIssue]
