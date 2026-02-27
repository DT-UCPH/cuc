"""Normalize frequent `l + body-part` compound-preposition sequences."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.config.l_body_compound_prep_rules import (
    L_BODY_COMPOUND_PREP_RULES,
    LBodyCompoundPrepRule,
)
from pipeline.config.l_negation_exception_refs import extract_separator_ref
from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line


def _is_l_i_row(row: TabletRow) -> bool:
    return (
        row.surface.strip() == "l"
        and row.analysis.strip() == "l(I)"
        and row.dulat.strip() == "l (I)"
    )


def _matches_second_rule_row(row: TabletRow, rule: LBodyCompoundPrepRule) -> bool:
    return row.analysis.strip() == rule.second_analysis and row.dulat.strip() == rule.second_dulat


def _forced_l_i_row(source: TabletRow) -> TabletRow:
    return TabletRow(
        line_id=source.line_id,
        surface=source.surface,
        analysis="l(I)",
        dulat="l (I)",
        pos="prep.",
        gloss="to",
        comment=source.comment,
    )


def _forced_second_row(source: TabletRow, rule: LBodyCompoundPrepRule) -> TabletRow:
    return TabletRow(
        line_id=source.line_id,
        surface=source.surface,
        analysis=rule.second_analysis,
        dulat=rule.second_dulat,
        pos=rule.second_pos,
        gloss=rule.second_gloss,
        comment=source.comment,
    )


@dataclass(frozen=True)
class _TokenGroup:
    key: tuple[str, str]
    indexes: list[int]
    rows: list[TabletRow]


class LBodyCompoundPrepDisambiguator(RefinementStep):
    """Force canonical payload for selected `l + X` compound-preposition sequences."""

    @property
    def name(self) -> str:
        return "l-body-compound-prep"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        parsed_rows: dict[int, TabletRow] = {}
        data_indexes: list[int] = []

        for index, raw in enumerate(lines):
            separator_ref = extract_separator_ref(raw)
            if separator_ref is not None:
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            parsed_rows[index] = row
            data_indexes.append(index)

        groups = self._group_rows(data_indexes=data_indexes, parsed_rows=parsed_rows)
        remove_indexes: set[int] = set()
        replace_rows: dict[int, TabletRow] = {}

        for idx, group in enumerate(groups):
            if group.key[1] != "l":
                continue
            next_group = groups[idx + 1] if idx + 1 < len(groups) else None
            if next_group is None:
                continue
            rule = L_BODY_COMPOUND_PREP_RULES.get(next_group.key[1])
            if rule is None:
                continue
            if not any(_matches_second_rule_row(row, rule) for row in next_group.rows):
                continue

            l_target_indexes = [
                row_index for row_index, row in zip(group.indexes, group.rows) if _is_l_i_row(row)
            ]
            keep_l_index = l_target_indexes[0] if l_target_indexes else group.indexes[0]
            forced_l = _forced_l_i_row(parsed_rows[keep_l_index])
            if forced_l.to_tsv() != parsed_rows[keep_l_index].to_tsv():
                replace_rows[keep_l_index] = forced_l
            remove_indexes.update(
                row_index for row_index in group.indexes if row_index != keep_l_index
            )

            second_target_indexes = [
                row_index
                for row_index, row in zip(next_group.indexes, next_group.rows)
                if _matches_second_rule_row(row, rule)
            ]
            keep_second_index = (
                second_target_indexes[0] if second_target_indexes else next_group.indexes[0]
            )
            forced_second = _forced_second_row(parsed_rows[keep_second_index], rule)
            if forced_second.to_tsv() != parsed_rows[keep_second_index].to_tsv():
                replace_rows[keep_second_index] = forced_second
            remove_indexes.update(
                row_index for row_index in next_group.indexes if row_index != keep_second_index
            )

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
    ) -> list[_TokenGroup]:
        groups: list[_TokenGroup] = []
        current_key: tuple[str, str] | None = None
        current_indexes: list[int] = []
        current_rows: list[TabletRow] = []

        for index in data_indexes:
            row = parsed_rows[index]
            key = (row.line_id.strip(), row.surface.strip())
            if current_key is None or key == current_key:
                current_key = key
                current_indexes.append(index)
                current_rows.append(row)
                continue

            groups.append(_TokenGroup(key=current_key, indexes=current_indexes, rows=current_rows))
            current_key = key
            current_indexes = [index]
            current_rows = [row]

        if current_key is not None:
            groups.append(_TokenGroup(key=current_key, indexes=current_indexes, rows=current_rows))
        return groups
