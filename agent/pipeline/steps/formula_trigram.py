"""Normalize hardcoded frequent three-token formula parses."""

from pathlib import Path

from pipeline.config.formula_trigram_rules import (
    FORMULA_TRIGRAM_RULES,
    FormulaTrigramRule,
    TokenParse,
)
from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    is_unresolved,
    parse_tsv_line,
)


def _split_variants(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(";") if v.strip()]


def _target_supported(row: TabletRow, target: TokenParse) -> bool:
    dulat_options = set(_split_variants(row.dulat))
    return target.dulat in dulat_options


def _has_variants(row: TabletRow) -> bool:
    return ";" in row.analysis or ";" in row.dulat or ";" in row.pos or ";" in row.gloss


class FormulaTrigramFixer(RefinementStep):
    """Apply hardcoded formula-trigram parsing normalizations."""

    def __init__(self, rules: tuple[FormulaTrigramRule, ...] | None = None) -> None:
        self._rules = tuple(rules or FORMULA_TRIGRAM_RULES)

    @property
    def name(self) -> str:
        return "formula-trigram"

    def refine_row(self, row: TabletRow) -> TabletRow:
        # Context-aware logic implemented in refine_file.
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        rows_processed = 0
        rows_changed = 0

        parsed_by_index: dict[int, TabletRow] = {}
        data_indexes: list[int] = []
        for idx, raw in enumerate(lines):
            if is_separator_line(raw) or not raw.strip():
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            parsed_by_index[idx] = row
            data_indexes.append(idx)

        next_index: dict[int, int | None] = {}
        third_index: dict[int, int | None] = {}
        for order_idx, idx in enumerate(data_indexes):
            nidx = data_indexes[order_idx + 1] if order_idx + 1 < len(data_indexes) else None
            tidx = data_indexes[order_idx + 2] if order_idx + 2 < len(data_indexes) else None
            next_index[idx] = nidx
            third_index[idx] = tidx

        overridden: dict[int, TabletRow] = {}
        for idx in data_indexes:
            first = parsed_by_index[idx]
            if is_unresolved(first):
                continue
            nidx = next_index.get(idx)
            tidx = third_index.get(idx)
            if nidx is None or tidx is None:
                continue
            second = parsed_by_index[nidx]
            third = parsed_by_index[tidx]
            if is_unresolved(second) or is_unresolved(third):
                continue
            out_first, out_second, out_third = self._apply_rules(first, second, third)
            if out_first.to_tsv() != first.to_tsv():
                overridden[idx] = out_first
            if out_second.to_tsv() != second.to_tsv():
                overridden[nidx] = out_second
            if out_third.to_tsv() != third.to_tsv():
                overridden[tidx] = out_third

        for idx, raw in enumerate(lines):
            row = parsed_by_index.get(idx)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            if is_unresolved(row):
                out_lines.append(raw)
                continue

            refined = overridden.get(idx, row)
            new_line = refined.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _apply_rules(
        self,
        first: TabletRow,
        second: TabletRow,
        third: TabletRow,
    ) -> tuple[TabletRow, TabletRow, TabletRow]:
        first_surface = first.surface.strip()
        second_surface = second.surface.strip()
        third_surface = third.surface.strip()
        out_first = first
        out_second = second
        out_third = third
        for rule in self._rules:
            if (
                first_surface != rule.first_surface
                or second_surface != rule.second_surface
                or third_surface != rule.third_surface
            ):
                continue
            if rule.first_target is not None:
                out_first = self._apply_target(out_first, rule.first_target)
            if rule.second_target is not None:
                out_second = self._apply_target(out_second, rule.second_target)
            if rule.third_target is not None:
                out_third = self._apply_target(out_third, rule.third_target)
            break
        return out_first, out_second, out_third

    def _apply_target(self, row: TabletRow, target: TokenParse) -> TabletRow:
        if not _target_supported(row, target):
            return row
        if (
            row.analysis == target.analysis
            and row.dulat == target.dulat
            and row.pos == target.pos
            and row.gloss == target.gloss
        ):
            return row
        if not _has_variants(row):
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=target.analysis,
            dulat=target.dulat,
            pos=target.pos,
            gloss=target.gloss,
            comment=row.comment,
        )
