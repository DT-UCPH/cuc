"""Contextual disambiguation rules for `ydk`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)


@dataclass(frozen=True)
class _RowGroup:
    """Contiguous rows sharing the same `(id, surface)` key."""

    key: tuple[str, str]
    indexes: list[int]
    rows: list[TabletRow]


class YdkContextDisambiguator(RefinementStep):
    """Apply targeted contextual disambiguation for `ydk`."""

    @property
    def name(self) -> str:
        return "ydk-context-disambiguator"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        parsed_rows: dict[int, TabletRow] = {}
        data_indexes: list[int] = []

        for index, raw in enumerate(lines):
            row = parse_tsv_line(raw)
            if row is None:
                continue
            parsed_rows[index] = row
            data_indexes.append(index)

        groups = self._group_rows(data_indexes=data_indexes, parsed_rows=parsed_rows)
        group_by_first_index = {group.indexes[0]: group for group in groups}
        replacement_by_first_index: dict[int, list[TabletRow]] = {}
        skip_indexes: set[int] = set()

        for idx, group in enumerate(groups):
            replacement = self._replacement_for_group(
                group=group, next_group=groups[idx + 1 : idx + 2]
            )
            if replacement is None:
                continue
            first = group.indexes[0]
            replacement_by_first_index[first] = replacement
            skip_indexes.update(group.indexes[1:])

        rows_processed = len(data_indexes)
        rows_changed = 0
        out_lines: list[str] = []

        for index, raw in enumerate(lines):
            if index in skip_indexes:
                continue

            replacement_rows = replacement_by_first_index.get(index)
            if replacement_rows is not None:
                group = group_by_first_index[index]
                original = [lines[i] for i in group.indexes]
                replacement_lines = [row.to_tsv() for row in replacement_rows]
                if replacement_lines != original:
                    rows_changed += len(group.indexes)
                out_lines.extend(replacement_lines)
                continue

            if is_separator_line(raw):
                out_lines.append(normalize_separator_row(raw))
                continue
            out_lines.append(raw)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _group_rows(
        self, data_indexes: list[int], parsed_rows: dict[int, TabletRow]
    ) -> list[_RowGroup]:
        groups: list[_RowGroup] = []
        current_indexes: list[int] = []
        current_rows: list[TabletRow] = []
        current_key: tuple[str, str] | None = None

        for index in data_indexes:
            row = parsed_rows[index]
            key = (row.line_id.strip(), row.surface.strip())
            if current_key is None or key == current_key:
                current_key = key
                current_indexes.append(index)
                current_rows.append(row)
                continue

            groups.append(_RowGroup(key=current_key, indexes=current_indexes, rows=current_rows))
            current_key = key
            current_indexes = [index]
            current_rows = [row]

        if current_key is not None:
            groups.append(_RowGroup(key=current_key, indexes=current_indexes, rows=current_rows))
        return groups

    def _replacement_for_group(
        self, group: _RowGroup, next_group: list[_RowGroup]
    ) -> list[TabletRow] | None:
        surface = group.key[1]
        next_surface = next_group[0].key[1] if next_group else ""
        if surface != "ydk" or next_surface != "ṣġr":
            return None

        base_row = group.rows[0]
        replacement = TabletRow(
            line_id=base_row.line_id,
            surface=base_row.surface,
            analysis="yd(II)/+k=",
            dulat="yd (II)",
            pos="n. m.",
            gloss="love",
            comment=base_row.comment,
        )
        return [replacement]
