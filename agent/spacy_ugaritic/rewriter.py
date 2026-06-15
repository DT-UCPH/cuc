"""Helpers for rewriting TSV files from spaCy-resolved token candidates."""

from __future__ import annotations

from collections.abc import Sequence

from spacy.tokens import Doc

from pipeline.steps.base import parse_tsv_line
from spacy_ugaritic.types import TabletToken


def count_data_rows(lines: Sequence[str]) -> int:
    """Return the number of parseable data rows in a TSV file."""
    return sum(1 for line in lines if parse_tsv_line(line) is not None)


def render_resolved_lines(
    lines: Sequence[str],
    tokens: Sequence[TabletToken],
    doc: Doc,
) -> tuple[list[str], int]:
    """Render output TSV lines and a line-level changed-row count."""
    token_entries = list(zip(tokens, doc, strict=True))
    first_index_to_token = {
        tablet_token.row_indexes[0]: (tablet_token, token) for tablet_token, token in token_entries
    }
    skipped_indexes = {
        row_index for tablet_token in tokens for row_index in tablet_token.row_indexes[1:]
    }
    out_lines: list[str] = []
    rows_changed = 0

    for row_index, raw in enumerate(lines):
        token_entry = first_index_to_token.get(row_index)
        if token_entry is not None:
            tablet_token, token = token_entry
            resolved_candidates = token._.resolved_candidates
            rendered_rows = [
                candidate.to_row(
                    line_id=tablet_token.line_id,
                    surface=tablet_token.surface,
                ).to_tsv()
                for candidate in resolved_candidates
            ]
            original_rows = [lines[index] for index in tablet_token.row_indexes]
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
