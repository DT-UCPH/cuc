"""Helpers for rewriting TSV files from spaCy-resolved row docs."""

from __future__ import annotations

from collections.abc import Sequence

from spacy.tokens import Doc

from pipeline.steps.base import parse_tsv_line


def count_data_rows(lines: Sequence[str]) -> int:
    """Return the number of parseable data rows in a TSV file."""
    return sum(1 for line in lines if parse_tsv_line(line) is not None)


def render_resolved_rows(lines: Sequence[str], doc: Doc) -> tuple[list[str], int]:
    """Render output lines and a changed-row count from a row-level doc."""
    out_lines = list(lines)
    rows_changed = 0
    for token in doc:
        line_index = token._.line_index
        row = token._.row
        resolved_row = token._.resolved_row or row
        if row is None or line_index < 0:
            continue
        new_line = resolved_row.to_tsv()
        if out_lines[line_index] != new_line:
            rows_changed += 1
            out_lines[line_index] = new_line
    return out_lines, rows_changed
