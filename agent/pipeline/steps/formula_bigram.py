"""Normalize hardcoded frequent two-token formula parses."""

from pathlib import Path

from pipeline.config.formula_bigram_rules import FORMULA_BIGRAM_RULES, FormulaBigramRule, TokenParse
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
    # Hard safety check: do not rewrite to unrelated lemmas.
    dulat_options = set(_split_variants(row.dulat))
    if target.dulat not in dulat_options:
        return False
    return True


class FormulaBigramFixer(RefinementStep):
    """Apply hardcoded formula-bigram parsing normalizations."""

    def __init__(self, rules: tuple[FormulaBigramRule, ...] | None = None) -> None:
        self._rules = tuple(rules or FORMULA_BIGRAM_RULES)

    @property
    def name(self) -> str:
        return "formula-bigram"

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
        for order_idx, idx in enumerate(data_indexes):
            next_index[idx] = (
                data_indexes[order_idx + 1] if order_idx + 1 < len(data_indexes) else None
            )

        overridden: dict[int, TabletRow] = {}
        for idx in data_indexes:
            row = parsed_by_index[idx]
            if is_unresolved(row):
                continue
            nidx = next_index.get(idx)
            if nidx is None:
                continue
            next_row = parsed_by_index[nidx]
            if is_unresolved(next_row):
                continue
            first, second = self._apply_rules(row, next_row)
            if first.to_tsv() != row.to_tsv():
                overridden[idx] = first
            if second.to_tsv() != next_row.to_tsv():
                overridden[nidx] = second

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

    def _apply_rules(self, first: TabletRow, second: TabletRow) -> tuple[TabletRow, TabletRow]:
        first_surface = first.surface.strip()
        second_surface = second.surface.strip()
        out_first = first
        out_second = second
        for rule in self._rules:
            if first_surface != rule.first_surface or second_surface != rule.second_surface:
                continue
            if rule.first_target is not None:
                out_first = self._apply_target(out_first, rule.first_target)
            if rule.second_target is not None:
                out_second = self._apply_target(out_second, rule.second_target)
            break
        return out_first, out_second

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
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=target.analysis,
            dulat=target.dulat,
            pos=target.pos,
            gloss=target.gloss,
            comment=row.comment,
        )
