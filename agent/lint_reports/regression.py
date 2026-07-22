"""Stable comparison of morphology linter errors across token renumbering."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

_ISSUE_RE = re.compile(
    r"^(?P<level>ERROR|WARNING|INFO)\s+(?P<file>.+?):(?P<line>\d+) (?P<details>.*)$"
)
_FIRST_SEEN_LINE_RE = re.compile(r"(?<=first seen on line) \d+")
_IDS_RE = re.compile(r"(?<=ids:) [^;)]+")
_LINES_RE = re.compile(r"(?<=lines:) [^;)]+")


@dataclass(frozen=True)
class RegressionIssue:
    """One linter issue with both diagnostic and comparison representations."""

    level: str
    file: str
    line_id: str
    surface: str
    message: str
    rendered: str

    @property
    def signature(self) -> tuple[str, str, str, str]:
        """Return an identity that deliberately excludes mutable row and token IDs."""
        return (
            self.level,
            normalize_issue_file(self.file),
            self.surface,
            normalize_regression_message(self.message),
        )


def normalize_issue_file(filename: str) -> str:
    """Keep a stable logical path while discarding temporary checkout prefixes."""
    normalized = filename.replace("\\", "/")
    marker = "auto_parsing/"
    marker_index = normalized.find(marker)
    if marker_index != -1:
        return normalized[marker_index:]
    return normalized.rsplit("/", maxsplit=1)[-1]


def normalize_regression_message(message: str) -> str:
    """Remove only row/token references that change during TF migrations."""
    normalized = _FIRST_SEEN_LINE_RE.sub(" <line>", message)
    normalized = _IDS_RE.sub(" <ids>", normalized)
    return _LINES_RE.sub(" <lines>", normalized)


def parse_lint_issues(lint_output: str, *, level: str = "ERROR") -> list[RegressionIssue]:
    """Parse linter text while preserving the original line for useful hook output."""
    issues: list[RegressionIssue] = []
    for raw_line in lint_output.splitlines():
        match = _ISSUE_RE.match(raw_line)
        if not match or match.group("level") != level:
            continue

        details = match.group("details")
        if details.startswith("  "):
            line_id = ""
            surface = ""
            message = details.lstrip()
        else:
            parts = details.split(maxsplit=2)
            if len(parts) < 3:
                line_id = ""
                surface = ""
                message = details.strip()
            else:
                line_id, surface, message = parts

        issues.append(
            RegressionIssue(
                level=match.group("level"),
                file=match.group("file"),
                line_id=line_id,
                surface=surface,
                message=message,
                rendered=raw_line,
            )
        )
    return issues


def read_lint_issues(path: Path, *, level: str = "ERROR") -> list[RegressionIssue]:
    """Read and parse one linter output file."""
    return parse_lint_issues(path.read_text(encoding="utf-8"), level=level)


def find_new_issues(
    baseline: list[RegressionIssue], candidate: list[RegressionIssue]
) -> list[RegressionIssue]:
    """Return candidate occurrences not covered by the baseline multiset."""
    remaining = Counter(issue.signature for issue in baseline)
    new_issues: list[RegressionIssue] = []
    for issue in candidate:
        if remaining[issue.signature] > 0:
            remaining[issue.signature] -= 1
        else:
            new_issues.append(issue)
    return new_issues
