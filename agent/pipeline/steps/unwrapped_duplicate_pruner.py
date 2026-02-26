"""Prune duplicate one-variant rows after unwrapping."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)


class UnwrappedDuplicatePruner(RefinementStep):
    """Drop duplicate rows with identical id/surface/col3-col6 payload."""

    @property
    def name(self) -> str:
        return "unwrapped-duplicate-pruner"

    def refine_row(self, row):  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        seen_payloads: set[tuple[str, str, str, str, str, str]] = set()
        rows_processed = 0
        rows_changed = 0

        for raw in lines:
            if not raw.strip():
                out_lines.append(raw)
                continue
            if is_separator_line(raw):
                out_lines.append(normalize_separator_row(raw))
                continue

            row = parse_tsv_line(raw)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            key = (
                row.line_id.strip(),
                row.surface.strip(),
                row.analysis.strip(),
                row.dulat.strip(),
                row.pos.strip(),
                row.gloss.strip(),
            )
            if key in seen_payloads:
                rows_changed += 1
                continue
            seen_payloads.add(key)
            out_lines.append(raw)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)
