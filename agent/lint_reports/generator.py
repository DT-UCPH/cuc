"""Report generation for morphology lint results."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from lint_reports.charts import SvgTrendPlotter
from lint_reports.parser import LintOutputParser, build_summary_markdown, stats_to_json_dict


class LintReportGenerator:
    """Runs linter with local DB access and materializes reports/ outputs."""

    def __init__(
        self,
        out_dir: Path,
        reports_dir: Path,
        dulat_db: Path,
        udb_db: Path,
        linter_path: Path,
    ) -> None:
        self.out_dir = out_dir
        self.reports_dir = reports_dir
        self.dulat_db = dulat_db
        self.udb_db = udb_db
        self.linter_path = linter_path
        self.parser = LintOutputParser()
        self.plotter = SvgTrendPlotter()

    def run(self) -> int:
        files = sorted(self.out_dir.glob("*.tsv"))
        if not files:
            raise RuntimeError("No TSV files found under out/.")
        if not self.dulat_db.exists():
            raise RuntimeError("Missing DULAT sqlite: %s" % self.dulat_db)
        if not self.udb_db.exists():
            raise RuntimeError("Missing UDB sqlite: %s" % self.udb_db)

        self.reports_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(self.linter_path),
            "--input-format",
            "labeled",
            "--dulat",
            str(self.dulat_db),
            "--udb",
            str(self.udb_db),
        ] + [str(item) for item in files]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        lint_output = result.stdout
        lint_stderr = result.stderr

        (self.reports_dir / "lint_report.txt").write_text(lint_output, encoding="utf-8")
        (self.reports_dir / "lint_stderr.txt").write_text(lint_stderr, encoding="utf-8")

        stats = self.parser.parse(lint_output=lint_output, files_checked=len(files))
        summary_markdown = build_summary_markdown(stats)
        (self.reports_dir / "lint_summary.md").write_text(summary_markdown, encoding="utf-8")

        generated_at = datetime.now(timezone.utc).isoformat()
        stats_payload = stats_to_json_dict(stats, generated_at_utc=generated_at)
        self._write_json(self.reports_dir / "lint_stats.json", stats_payload)

        issue_type_counts = self._collapse_issue_types(stats_payload)
        history = self._load_history()
        history = self._upsert_history(history=history, stats=stats_payload, issue_type_counts=issue_type_counts)
        self._write_json(self.reports_dir / "lint_history.json", history)

        self._render_trends(history)

        return int(result.returncode)

    def _collapse_issue_types(self, stats_payload: Dict[str, object]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        items = stats_payload.get("by_problem_type") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            key = str(item.get("problem_type") or "").strip() or "(unknown)"
            value = int(item.get("count", 0) or 0)
            counts[key] = counts.get(key, 0) + value
        return counts

    def _load_history(self) -> List[Dict[str, object]]:
        path = self.reports_dir / "lint_history.json"
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload
        except Exception:
            return []
        return []

    def _upsert_history(
        self,
        history: List[Dict[str, object]],
        stats: Dict[str, object],
        issue_type_counts: Dict[str, int],
    ) -> List[Dict[str, object]]:
        head_sha = self._git_output(["rev-parse", "--short=12", "HEAD"])
        branch = self._git_output(["rev-parse", "--abbrev-ref", "HEAD"])

        signature_source = {
            "total_issues": stats.get("total_issues"),
            "by_severity": stats.get("by_severity"),
            "issue_types": issue_type_counts,
            "files_checked": stats.get("files_checked"),
        }
        signature = hashlib.sha1(json.dumps(signature_source, sort_keys=True).encode("utf-8")).hexdigest()

        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_head": head_sha,
            "git_branch": branch,
            "report_signature": signature,
            "files_checked": int(stats.get("files_checked", 0) or 0),
            "total_issues": int(stats.get("total_issues", 0) or 0),
            "by_severity": {
                "ERROR": int((stats.get("by_severity") or {}).get("ERROR", 0) or 0),
                "WARNING": int((stats.get("by_severity") or {}).get("WARNING", 0) or 0),
                "INFO": int((stats.get("by_severity") or {}).get("INFO", 0) or 0),
            },
            "issue_types": issue_type_counts,
        }

        if history:
            latest = history[-1]
            if (
                latest.get("report_signature") == signature
                and latest.get("git_head") == head_sha
            ):
                history[-1] = entry
                return history[-300:]

        history.append(entry)
        return history[-300:]

    def _render_trends(self, history: List[Dict[str, object]]) -> None:
        runs = history[-60:] if history else []
        if not runs:
            return

        x_labels = [str(idx + 1) for idx in range(len(runs))]
        severity_series = []
        for severity in ("ERROR", "WARNING", "INFO"):
            values = [int((run.get("by_severity") or {}).get(severity, 0) or 0) for run in runs]
            severity_series.append((severity, values))
        self.plotter.render(
            title="Morphology Lint Trend by Severity",
            x_labels=x_labels,
            series=severity_series,
            output_path=str(self.reports_dir / "lint_severity_trend.svg"),
        )

        totals: Dict[str, int] = {}
        for run in runs:
            for issue_type, count in (run.get("issue_types") or {}).items():
                totals[issue_type] = totals.get(issue_type, 0) + int(count or 0)
        top_issue_types = [
            item
            for item, _ in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
        ]
        issue_type_series = []
        for issue_type in top_issue_types:
            values = [int((run.get("issue_types") or {}).get(issue_type, 0) or 0) for run in runs]
            issue_type_series.append((issue_type, values))
        self.plotter.render(
            title="Morphology Lint Trend by Issue Type",
            x_labels=x_labels,
            series=issue_type_series,
            output_path=str(self.reports_dir / "lint_issue_types_trend.svg"),
            width=1300,
            height=560,
        )

        latest = runs[-1]
        trend_lines = []
        trend_lines.append("## Morphology Lint Trends")
        trend_lines.append("")
        trend_lines.append("- History points used: `%d`" % len(runs))
        trend_lines.append("- Latest git head: `%s`" % (latest.get("git_head") or ""))
        trend_lines.append("")
        trend_lines.append("### Current Severity Snapshot")
        trend_lines.append("")
        trend_lines.append("| Severity | Count |")
        trend_lines.append("|---|---:|")
        for severity in ("ERROR", "WARNING", "INFO"):
            trend_lines.append(
                "| %s | %d |"
                % (severity, int((latest.get("by_severity") or {}).get(severity, 0) or 0))
            )
        trend_lines.append("")
        trend_lines.append("### Plot Files")
        trend_lines.append("")
        trend_lines.append("- `reports/lint_severity_trend.svg`")
        trend_lines.append("- `reports/lint_issue_types_trend.svg`")
        (self.reports_dir / "lint_trends.md").write_text("\n".join(trend_lines) + "\n", encoding="utf-8")

    def _git_output(self, args: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            return ""
        if result.returncode != 0:
            return ""
        return (result.stdout or "").strip()

    def _write_json(self, path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
