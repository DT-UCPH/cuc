"""Helpers for rewriting TSV files from spaCy-resolved token candidates."""

from __future__ import annotations

from collections.abc import Sequence

from spacy.tokens import Doc

from pipeline.steps.base import parse_tsv_line
from spacy_ugaritic_types import GroupedToken


def count_data_rows(lines: Sequence[str]) -> int:
    """Return the number of parseable data rows in a TSV file."""
    return sum(1 for line in lines if parse_tsv_line(line) is not None)


def render_resolved_lines(
    lines: Sequence[str],
    grouped_tokens: Sequence[GroupedToken],
    doc: Doc,
) -> tuple[list[str], int]:
    """Render output TSV lines and a line-level changed-row count."""
    group_entries = list(zip(grouped_tokens, doc, strict=True))
    first_index_to_group = {group.row_indexes[0]: (group, token) for group, token in group_entries}
    skipped_indexes = {row_index for group in grouped_tokens for row_index in group.row_indexes[1:]}
    out_lines: list[str] = []
    rows_changed = 0

    for row_index, raw in enumerate(lines):
        group_entry = first_index_to_group.get(row_index)
        if group_entry is not None:
            group, token = group_entry
            resolved_candidates = token._.resolved_candidates or token._.candidates
            rendered_rows = [
                candidate.to_row(line_id=group.line_id, surface=group.surface).to_tsv()
                for candidate in resolved_candidates
            ]
            original_rows = [lines[index] for index in group.row_indexes]
            rows_changed += _count_group_row_changes(original_rows, rendered_rows)
            out_lines.extend(rendered_rows)
            continue
        if row_index in skipped_indexes:
            continue
        out_lines.append(raw)

    return out_lines, rows_changed


def _count_group_row_changes(original_rows: Sequence[str], rendered_rows: Sequence[str]) -> int:
    changed = 0
    shared_length = min(len(original_rows), len(rendered_rows))
    for index in range(shared_length):
        if original_rows[index] != rendered_rows[index]:
            changed += 1
    changed += abs(len(original_rows) - len(rendered_rows))
    return changed
