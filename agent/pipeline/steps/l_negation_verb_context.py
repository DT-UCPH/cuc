"""Prune `l(II)` negation readings when not followed by a verbal token."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.config.l_negation_exception_refs import (
    extract_separator_ref,
    is_forced_l_negation_ref,
)
from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line


def _is_l_negation_row(row: TabletRow) -> bool:
    return (
        row.surface.strip() == "l"
        and row.analysis.strip() == "l(II)"
        and row.dulat.strip() == "l (II)"
        and row.pos.strip() == "adv."
        and row.gloss.strip() in {"no", "not"}
    )


def _forced_l_negation_row(source: TabletRow) -> TabletRow:
    """Build a canonical forced `l(II)` row while preserving id/surface/comments."""
    return TabletRow(
        line_id=source.line_id,
        surface=source.surface,
        analysis="l(II)",
        dulat="l (II)",
        pos="adv.",
        gloss="no",
        comment=source.comment,
    )


@dataclass(frozen=True)
class _TokenGroup:
    key: tuple[str, str]
    section_ref: str
    indexes: list[int]
    rows: list[TabletRow]


class LNegationVerbContextPruner(RefinementStep):
    """Drop ambiguous `l(II)` rows unless the following token is verbal."""

    @property
    def name(self) -> str:
        return "l-negation-verb-context"

    def refine_row(self, row: TabletRow) -> TabletRow:
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        parsed_rows: dict[int, TabletRow] = {}
        section_refs: dict[int, str] = {}
        data_indexes: list[int] = []
        active_ref = ""
        for index, raw in enumerate(lines):
            separator_ref = extract_separator_ref(raw)
            if separator_ref is not None:
                active_ref = separator_ref
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            parsed_rows[index] = row
            section_refs[index] = active_ref
            data_indexes.append(index)

        groups = self._group_rows(
            data_indexes=data_indexes,
            parsed_rows=parsed_rows,
            section_refs=section_refs,
        )
        remove_indexes: set[int] = set()
        replace_rows: dict[int, TabletRow] = {}

        for idx, group in enumerate(groups):
            if group.key[1] != "l":
                continue
            l2_indexes = [
                row_index
                for row_index, row in zip(group.indexes, group.rows)
                if _is_l_negation_row(row)
            ]

            if is_forced_l_negation_ref(group.section_ref):
                keep_index = l2_indexes[0] if l2_indexes else group.indexes[0]
                if not l2_indexes:
                    replace_rows[keep_index] = _forced_l_negation_row(parsed_rows[keep_index])
                remove_indexes.update(
                    row_index for row_index in group.indexes if row_index != keep_index
                )
                continue

            next_group = groups[idx + 1] if idx + 1 < len(groups) else None
            next_has_verb = bool(
                next_group and any("vb" in (row.pos or "") for row in next_group.rows)
            )
            if next_has_verb:
                continue

            if not l2_indexes:
                continue
            # Do not delete the entire token if only one analysis exists.
            if len(l2_indexes) == len(group.indexes):
                continue
            remove_indexes.update(l2_indexes)

        if not remove_indexes and not replace_rows:
            return StepResult(file=path.name, rows_processed=len(data_indexes), rows_changed=0)

        out_lines: list[str] = []
        for index, raw in enumerate(lines):
            if index in remove_indexes:
                continue
            replacement = replace_rows.get(index)
            out_lines.append(raw if replacement is None else replacement.to_tsv())
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(
            file=path.name,
            rows_processed=len(data_indexes),
            rows_changed=len(remove_indexes) + len(replace_rows),
        )

    def _group_rows(
        self,
        data_indexes: list[int],
        parsed_rows: dict[int, TabletRow],
        section_refs: dict[int, str],
    ) -> list[_TokenGroup]:
        groups: list[_TokenGroup] = []
        current_key: tuple[str, str] | None = None
        current_section_ref = ""
        current_indexes: list[int] = []
        current_rows: list[TabletRow] = []

        for index in data_indexes:
            row = parsed_rows[index]
            key = (row.line_id.strip(), row.surface.strip())
            if current_key is None or key == current_key:
                current_key = key
                if not current_indexes:
                    current_section_ref = section_refs.get(index, "")
                current_indexes.append(index)
                current_rows.append(row)
                continue

            groups.append(
                _TokenGroup(
                    key=current_key,
                    section_ref=current_section_ref,
                    indexes=current_indexes,
                    rows=current_rows,
                )
            )
            current_key = key
            current_section_ref = section_refs.get(index, "")
            current_indexes = [index]
            current_rows = [row]

        if current_key is not None:
            groups.append(
                _TokenGroup(
                    key=current_key,
                    section_ref=current_section_ref,
                    indexes=current_indexes,
                    rows=current_rows,
                )
            )
        return groups
