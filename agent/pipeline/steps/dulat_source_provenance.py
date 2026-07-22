"""Annotate parser rows whose col4 entry comes from a non-DULAT source."""

from __future__ import annotations

from pathlib import Path

from pipeline.dulat_source_provenance import (
    DulatSourceProvenanceIndex,
    append_provenance_comments,
)
from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)


class DulatSourceProvenanceAnnotator(RefinementStep):
    """Add source comments for imported records in the DULAT database."""

    def __init__(self, dulat_db: Path) -> None:
        self._index = DulatSourceProvenanceIndex.from_sqlite(dulat_db)

    @property
    def name(self) -> str:
        return "dulat-source-provenance"

    def refine_row(self, row: TabletRow) -> TabletRow:
        sources = self._index.sources_for_field(row.dulat, row.gloss)
        if not sources:
            return row
        comment = append_provenance_comments(row.comment, sources)
        if comment == row.comment:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=row.analysis,
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=comment,
        )

    def refine_file(self, path: Path) -> StepResult:
        """Annotate resolved and unresolved rows that retain a col4 reference."""
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
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
            updated = self.refine_row(row)
            new_line = updated.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(path.name, rows_processed, rows_changed)
