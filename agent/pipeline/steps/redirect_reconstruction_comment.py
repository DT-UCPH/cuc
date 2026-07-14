"""Add a provenance comment to redirect-derived reconstructed variants."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)

_COMMENT = "Based on DULAT reconstruction."


def _append_comment(existing: str) -> str:
    text = (existing or "").strip()
    if not text:
        return _COMMENT
    if _COMMENT in text:
        return text
    return f"{text} {_COMMENT}"


class RedirectReconstructionCommentFixer(RefinementStep):
    """Mark reconstructed non-arrow rows in redirect ambiguity groups."""

    @property
    def name(self) -> str:
        return "redirect-reconstruction-comment"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()

        parsed_rows: list[TabletRow | None] = []
        redirect_groups: set[tuple[str, str]] = set()
        rows_processed = 0

        for raw in lines:
            if not raw.strip() or is_separator_line(raw):
                parsed_rows.append(None)
                continue
            row = parse_tsv_line(raw)
            parsed_rows.append(row)
            if row is None:
                continue
            rows_processed += 1
            if row.pos.strip() == "→":
                redirect_groups.add((row.line_id.strip(), row.surface.strip()))

        out_lines: list[str] = []
        rows_changed = 0

        for raw, row in zip(lines, parsed_rows):
            if not raw.strip():
                out_lines.append(raw)
                continue
            if is_separator_line(raw):
                out_lines.append(normalize_separator_row(raw))
                continue
            if row is None:
                out_lines.append(raw)
                continue

            key = (row.line_id.strip(), row.surface.strip())
            if key in redirect_groups and row.pos.strip() != "→":
                updated = TabletRow(
                    line_id=row.line_id,
                    surface=row.surface,
                    analysis=row.analysis,
                    dulat=row.dulat,
                    pos=row.pos,
                    gloss=row.gloss,
                    comment=_append_comment(row.comment),
                )
                new_line = updated.to_tsv()
                if new_line != raw:
                    rows_changed += 1
                out_lines.append(new_line)
                continue

            out_lines.append(raw)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)
