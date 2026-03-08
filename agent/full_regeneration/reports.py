"""Report writers for reviewed scoring and combined rerun deltas."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reviewed_evaluation import (
    EvaluationTargetResolver,
    MorphologyAgreementScorer,
    MorphologyTsvLoader,
)

_SCORING_SUMMARY_KEYS = (
    "compared_ids",
    "reviewed_option_count",
    "auto_option_count",
    "true_positive_option_count",
    "exact_set_accuracy",
    "macro_precision",
    "macro_recall",
    "macro_f1",
    "macro_jaccard",
    "micro_precision",
    "micro_recall",
    "micro_f1",
    "gold_coverage",
    "mean_extra_options",
    "mean_missing_options",
    "mean_option_count_error",
)
_SCORING_DELTA_KEYS = (
    "compared_ids",
    "exact_set_accuracy",
    "macro_f1",
    "micro_f1",
    "gold_coverage",
    "macro_precision",
    "macro_recall",
    "micro_precision",
    "micro_recall",
    "mean_extra_options",
    "mean_missing_options",
)
_PER_FILE_SCORING_KEYS = (
    "compared_ids",
    "exact_set_accuracy",
    "macro_f1",
    "micro_f1",
    "gold_coverage",
)


@dataclass(frozen=True)
class ScoringArtifacts:
    """Written scoring payloads plus before/after snapshots."""

    previous: dict[str, Any] | None
    current: dict[str, Any]


class ScoringReportWriter:
    """Generate reviewed morphology scoring reports and deltas."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir
        self._loader = MorphologyTsvLoader()
        self._resolver = EvaluationTargetResolver()
        self._scorer = MorphologyAgreementScorer()

    def generate(self, *, reviewed_root: Path, auto_root: Path) -> ScoringArtifacts:
        previous = self._load_json(self.reports_dir / "reviewed_morphology_report.json")
        self._write_previous_snapshot(previous)

        pairs = self._resolver.resolve(reviewed_root, auto_root)
        file_results = []
        for pair in pairs:
            reviewed = self._loader.load(pair.reviewed_path)
            auto = (
                self._loader.load(pair.auto_path)
                if pair.auto_path is not None
                else self._loader.empty(pair.label)
            )
            file_results.append(
                self._scorer.score_file_pair(label=pair.label, reviewed=reviewed, auto=auto)
            )

        aggregate = self._scorer.score_many(
            reviewed_root=reviewed_root,
            auto_root=auto_root,
            file_results=file_results,
        )
        payload = aggregate.to_dict()
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(self.reports_dir / "reviewed_morphology_report.current.json", payload)
        self._write_json(self.reports_dir / "reviewed_morphology_report.json", payload)
        (self.reports_dir / "reviewed_morphology_report.md").write_text(
            self._render_summary_markdown(payload),
            encoding="utf-8",
        )
        (self.reports_dir / "reviewed_morphology_report_delta.md").write_text(
            self._render_delta_markdown(previous=previous, current=payload),
            encoding="utf-8",
        )
        return ScoringArtifacts(previous=previous, current=payload)

    def _write_previous_snapshot(self, payload: dict[str, Any] | None) -> None:
        path = self.reports_dir / "reviewed_morphology_report.previous.json"
        if payload is None:
            if path.exists():
                path.unlink()
            return
        self._write_json(path, payload)

    def _render_summary_markdown(self, payload: dict[str, Any]) -> str:
        lines = ["# Reviewed Morphology Agreement", ""]
        lines.append(f"- Reviewed root: `{payload.get('reviewed_root', '')}`")
        lines.append(f"- Auto root: `{payload.get('auto_root', '')}`")
        lines.append(f"- Files scored: `{payload.get('file_count', 0)}`")
        lines.append("")
        lines.append("## Overall")
        lines.append("")
        lines.extend(self._render_metric_table(payload.get("summary") or {}))
        lines.append("")
        lines.append("## Per File")
        lines.append("")
        lines.append("| File | Ids | Exact | Macro F1 | Micro F1 | Coverage |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for item in payload.get("files") or []:
            summary = item.get("summary") or {}
            lines.append(
                "| %s | %s | %.4f | %.4f | %.4f | %.4f |"
                % (
                    item.get("label", ""),
                    summary.get("compared_ids", 0),
                    float(summary.get("exact_set_accuracy", 0.0) or 0.0),
                    float(summary.get("macro_f1", 0.0) or 0.0),
                    float(summary.get("micro_f1", 0.0) or 0.0),
                    float(summary.get("gold_coverage", 0.0) or 0.0),
                )
            )
        return "\n".join(lines) + "\n"

    def _render_delta_markdown(
        self,
        *,
        previous: dict[str, Any] | None,
        current: dict[str, Any],
    ) -> str:
        lines = ["# Reviewed Morphology Score Delta", ""]
        lines.append("Previous report: `agent/reports/reviewed_morphology_report.previous.json`")
        lines.append("Current report: `agent/reports/reviewed_morphology_report.current.json`")
        if previous is None:
            lines.append("")
            lines.append("No previous scoring snapshot was available.")
            return "\n".join(lines) + "\n"

        lines.append("")
        lines.append("## Overall Delta")
        lines.append("")
        lines.append("| Metric | Previous | Current | Delta |")
        lines.append("| --- | ---: | ---: | ---: |")
        prev_summary = previous.get("summary") or {}
        curr_summary = current.get("summary") or {}
        for key in _SCORING_SUMMARY_KEYS:
            prev_value = prev_summary.get(key, 0)
            curr_value = curr_summary.get(key, 0)
            lines.append(
                "| %s | %s | %s | %s |"
                % (
                    key,
                    _fmt_value(prev_value),
                    _fmt_value(curr_value),
                    _fmt_delta(curr_value, prev_value),
                )
            )

        lines.append("")
        lines.append("## Per File Delta")
        lines.append("")
        lines.append(
            "| File | Prev ids | Curr ids | Δ ids | Prev macro F1 | Curr macro F1 | "
            "Δ macro F1 | Prev micro F1 | Curr micro F1 | Δ micro F1 | "
            "Prev coverage | Curr coverage | Δ coverage |"
        )
        lines.append(
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: | ---: | ---: |"
        )
        prev_files = {item.get("label", ""): item for item in previous.get("files") or []}
        curr_files = {item.get("label", ""): item for item in current.get("files") or []}
        for label in sorted(set(prev_files) | set(curr_files)):
            prev_summary = prev_files.get(label, {}).get("summary") or {}
            curr_summary = curr_files.get(label, {}).get("summary") or {}
            prev_ids = int(prev_summary.get("compared_ids", 0) or 0)
            curr_ids = int(curr_summary.get("compared_ids", 0) or 0)
            lines.append(
                "| %s | %d | %d | %+d | %.4f | %.4f | %+0.4f | %.4f | %.4f | "
                "%+0.4f | %.4f | %.4f | %+0.4f |"
                % (
                    label,
                    prev_ids,
                    curr_ids,
                    curr_ids - prev_ids,
                    float(prev_summary.get("macro_f1", 0.0) or 0.0),
                    float(curr_summary.get("macro_f1", 0.0) or 0.0),
                    float(curr_summary.get("macro_f1", 0.0) or 0.0)
                    - float(prev_summary.get("macro_f1", 0.0) or 0.0),
                    float(prev_summary.get("micro_f1", 0.0) or 0.0),
                    float(curr_summary.get("micro_f1", 0.0) or 0.0),
                    float(curr_summary.get("micro_f1", 0.0) or 0.0)
                    - float(prev_summary.get("micro_f1", 0.0) or 0.0),
                    float(prev_summary.get("gold_coverage", 0.0) or 0.0),
                    float(curr_summary.get("gold_coverage", 0.0) or 0.0),
                    float(curr_summary.get("gold_coverage", 0.0) or 0.0)
                    - float(prev_summary.get("gold_coverage", 0.0) or 0.0),
                )
            )
        return "\n".join(lines) + "\n"

    def _render_metric_table(self, summary: dict[str, Any]) -> list[str]:
        lines = ["| Metric | Value |", "| --- | ---: |"]
        for key in _SCORING_SUMMARY_KEYS:
            lines.append("| %s | %s |" % (key, _fmt_value(summary.get(key, 0))))
        return lines

    def _load_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RerunDeltaWriter:
    """Write a combined lint/scoring rerun delta summary."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir

    def write(
        self,
        *,
        lint_before: dict[str, Any] | None,
        lint_after: dict[str, Any] | None,
        scoring_before: dict[str, Any] | None,
        scoring_after: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._build_payload(
            lint_before=lint_before,
            lint_after=lint_after,
            scoring_before=scoring_before,
            scoring_after=scoring_after,
        )
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        (self.reports_dir / "rerun_delta_summary.md").write_text(
            self._render_markdown(payload),
            encoding="utf-8",
        )
        (self.reports_dir / "rerun_delta_summary.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return payload

    def snapshot_previous_lint_reports(self) -> dict[str, Any] | None:
        previous = self._load_json(self.reports_dir / "lint_stats.json")
        self._copy_if_exists("lint_stats.json", "lint_stats.before_latest.json")
        self._copy_if_exists("lint_history.json", "lint_history.before_latest.json")
        self._copy_if_exists("lint_report.txt", "lint_report.before_latest.txt")
        return previous

    def _build_payload(
        self,
        *,
        lint_before: dict[str, Any] | None,
        lint_after: dict[str, Any] | None,
        scoring_before: dict[str, Any] | None,
        scoring_after: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "lint_before": _compact_lint_stats(lint_before),
            "lint_after": _compact_lint_stats(lint_after),
            "lint_delta": _lint_delta(lint_before, lint_after),
            "largest_problem_deltas": _largest_problem_deltas(lint_before, lint_after),
            "scoring_before": (scoring_before or {}).get("summary"),
            "scoring_after": (scoring_after or {}).get("summary"),
            "scoring_delta": _scoring_delta(scoring_before, scoring_after),
            "per_file_scoring_delta": _per_file_scoring_delta(scoring_before, scoring_after),
        }
        return payload

    def _render_markdown(self, payload: dict[str, Any]) -> str:
        lines = ["# Rerun Delta Summary", ""]
        lines.append(f"- Generated: `{payload.get('generated_at_utc', '')}`")

        lint_before = payload.get("lint_before")
        lint_after = payload.get("lint_after")
        lint_delta = payload.get("lint_delta")
        lines.append("")
        lines.append("## Lint")
        lines.append("")
        if not lint_before or not lint_after or not lint_delta:
            lines.append("No previous lint snapshot was available.")
        else:
            lines.append(
                "- Total issues: `%s` -> `%s` (%s)"
                % (
                    lint_before.get("total_issues", 0),
                    lint_after.get("total_issues", 0),
                    _fmt_signed_int(lint_delta.get("total_issues", 0)),
                )
            )
            for severity in ("ERROR", "INFO", "WARNING"):
                lines.append(
                    "- `%s`: `%s` -> `%s` (%s)"
                    % (
                        severity,
                        (lint_before.get("by_severity") or {}).get(severity, 0),
                        (lint_after.get("by_severity") or {}).get(severity, 0),
                        _fmt_signed_int(
                            ((lint_delta.get("by_severity") or {}).get(severity, 0) or 0)
                        ),
                    )
                )
            problem_deltas = payload.get("largest_problem_deltas") or []
            if problem_deltas:
                lines.append("")
                lines.append("Largest problem-type deltas")
                lines.append("")
                for item in problem_deltas:
                    lines.append(
                        "- `%s` `%s`: `%s` -> `%s` (%s)"
                        % (
                            item.get("severity", ""),
                            item.get("problem_type", ""),
                            item.get("before", 0),
                            item.get("after", 0),
                            _fmt_signed_int(int(item.get("delta", 0) or 0)),
                        )
                    )

        lines.append("")
        lines.append("## Scoring")
        lines.append("")
        scoring_before = payload.get("scoring_before")
        scoring_after = payload.get("scoring_after")
        scoring_delta = payload.get("scoring_delta")
        if not scoring_before or not scoring_after or not scoring_delta:
            lines.append("No previous scoring snapshot was available.")
        else:
            for key in (
                "compared_ids",
                "exact_set_accuracy",
                "macro_f1",
                "micro_f1",
                "gold_coverage",
            ):
                lines.append(
                    "- `%s`: `%s` -> `%s` (%s)"
                    % (
                        key,
                        _fmt_value(scoring_before.get(key, 0)),
                        _fmt_value(scoring_after.get(key, 0)),
                        _fmt_delta(scoring_after.get(key, 0), scoring_before.get(key, 0)),
                    )
                )
            per_file = payload.get("per_file_scoring_delta") or {}
            if per_file:
                lines.append("")
                lines.append("Per file scoring deltas")
                lines.append("")
                for label in sorted(per_file):
                    item = per_file[label]
                    lines.append(
                        "- `%s`: exact `%s`, macro F1 `%s`, micro F1 `%s`, coverage `%s`, ids `%s`"
                        % (
                            label,
                            _fmt_delta(item.get("exact_set_accuracy", 0), 0),
                            _fmt_delta(item.get("macro_f1", 0), 0),
                            _fmt_delta(item.get("micro_f1", 0), 0),
                            _fmt_delta(item.get("gold_coverage", 0), 0),
                            _fmt_signed_int(int(item.get("compared_ids", 0) or 0)),
                        )
                    )
        return "\n".join(lines) + "\n"

    def _load_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def _copy_if_exists(self, source_name: str, target_name: str) -> None:
        source = self.reports_dir / source_name
        target = self.reports_dir / target_name
        if source.exists():
            shutil.copyfile(source, target)


def _compact_lint_stats(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if payload is None:
        return None
    return {
        "total_issues": int(payload.get("total_issues", 0) or 0),
        "by_severity": {
            severity: int(((payload.get("by_severity") or {}).get(severity, 0) or 0))
            for severity in ("ERROR", "WARNING", "INFO")
        },
    }


def _lint_delta(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if before is None or after is None:
        return None
    return {
        "total_issues": int(after.get("total_issues", 0) or 0)
        - int(before.get("total_issues", 0) or 0),
        "by_severity": {
            severity: int(((after.get("by_severity") or {}).get(severity, 0) or 0))
            - int(((before.get("by_severity") or {}).get(severity, 0) or 0))
            for severity in ("ERROR", "WARNING", "INFO")
        },
    }


def _largest_problem_deltas(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    if before is None or after is None:
        return []
    prev = _problem_count_map(before)
    curr = _problem_count_map(after)
    deltas: list[dict[str, Any]] = []
    for key in sorted(set(prev) | set(curr)):
        before_count = prev.get(key, 0)
        after_count = curr.get(key, 0)
        delta = after_count - before_count
        if delta == 0:
            continue
        severity, problem_type = key
        deltas.append(
            {
                "severity": severity,
                "problem_type": problem_type,
                "delta": delta,
                "before": before_count,
                "after": after_count,
            }
        )
    deltas.sort(key=lambda item: (-abs(int(item["delta"])), item["severity"], item["problem_type"]))
    return deltas[:limit]


def _problem_count_map(payload: dict[str, Any]) -> dict[tuple[str, str], int]:
    mapping: dict[tuple[str, str], int] = {}
    for item in payload.get("by_problem_type") or []:
        if not isinstance(item, dict):
            continue
        key = (
            str(item.get("severity", "") or ""),
            str(item.get("problem_type", "") or ""),
        )
        mapping[key] = int(item.get("count", 0) or 0)
    return mapping


def _scoring_delta(
    before: dict[str, Any] | None,
    after: dict[str, Any],
) -> dict[str, Any] | None:
    if before is None:
        return None
    prev_summary = before.get("summary") or {}
    curr_summary = after.get("summary") or {}
    return {
        key: _numeric_delta(curr_summary.get(key, 0), prev_summary.get(key, 0))
        for key in _SCORING_DELTA_KEYS
    }


def _per_file_scoring_delta(
    before: dict[str, Any] | None,
    after: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    if before is None:
        return {}
    prev_files = {item.get("label", ""): item for item in before.get("files") or []}
    curr_files = {item.get("label", ""): item for item in after.get("files") or []}
    payload: dict[str, dict[str, Any]] = {}
    for label in sorted(set(prev_files) | set(curr_files)):
        prev_summary = prev_files.get(label, {}).get("summary") or {}
        curr_summary = curr_files.get(label, {}).get("summary") or {}
        payload[label] = {
            key: _numeric_delta(curr_summary.get(key, 0), prev_summary.get(key, 0))
            for key in _PER_FILE_SCORING_KEYS
        }
    return payload


def _numeric_delta(current: Any, previous: Any) -> float | int:
    curr = current or 0
    prev = previous or 0
    if isinstance(curr, int) and isinstance(prev, int):
        return curr - prev
    return float(curr) - float(prev)


def _fmt_signed_int(value: int) -> str:
    return f"{value:+d}"


def _fmt_value(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    return f"{float(value or 0.0):.4f}"


def _fmt_delta(current: Any, previous: Any) -> str:
    delta = _numeric_delta(current, previous)
    if isinstance(delta, int):
        return _fmt_signed_int(delta)
    return f"{float(delta):+0.4f}"
