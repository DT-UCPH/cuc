"""Drop unreconstructable host-only function-word rows when a clitic sibling exists."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)

_ALLOWED_POS_PREFIXES = (
    "prep.",
    "adv.",
    "conj.",
    "functor",
    "det.",
)


def _pos_head(value: str) -> str:
    return ((value or "").split(",", 1)[0]).strip().lower()


def _reconstructed(row: TabletRow) -> str:
    return normalize_surface(reconstruct_surface_from_analysis(row.analysis or "")).lower()


def _is_clitic_analysis(analysis: str) -> bool:
    value = (analysis or "").strip()
    return "+" in value or "~" in value


class FunctionWordCliticPruner(RefinementStep):
    """Prune shorter host-only rows once the same lexeme is encoded with a clitic."""

    @property
    def name(self) -> str:
        return "function-word-clitic-pruner"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        rows_processed = 0
        rows_changed = 0
        group: list[tuple[str, TabletRow]] = []
        group_key: tuple[str, str] | None = None

        def flush_group() -> None:
            nonlocal rows_changed, rows_processed, group, group_key
            if not group:
                return
            rows_processed += len(group)
            kept = self._prune_group([row for _, row in group])
            rows_changed += len(group) - len(kept)
            out_lines.extend(row.to_tsv() for row in kept)
            group = []
            group_key = None

        for raw in lines:
            if not raw.strip():
                flush_group()
                out_lines.append(raw)
                continue
            if is_separator_line(raw):
                flush_group()
                out_lines.append(normalize_separator_row(raw))
                continue

            row = parse_tsv_line(raw)
            if row is None:
                flush_group()
                out_lines.append(raw)
                continue

            key = (row.line_id.strip(), row.surface.strip())
            if group_key is not None and key != group_key:
                flush_group()
            group_key = key
            group.append((raw, row))

        flush_group()
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _prune_group(self, rows: list[TabletRow]) -> list[TabletRow]:
        if len(rows) < 2:
            return rows
        surface_norm = normalize_surface(rows[0].surface).lower()
        clitic_rows: list[TabletRow] = []
        for row in rows:
            if _reconstructed(row) == surface_norm and _is_clitic_analysis(row.analysis):
                clitic_rows.append(row)
        if not clitic_rows:
            return rows

        kept: list[TabletRow] = []
        for row in rows:
            reconstructed = _reconstructed(row)
            pos_head = _pos_head(row.pos)
            if not any(pos_head.startswith(prefix) for prefix in _ALLOWED_POS_PREFIXES):
                kept.append(row)
                continue
            if _is_clitic_analysis(row.analysis):
                kept.append(row)
                continue
            if (
                not reconstructed
                or reconstructed == surface_norm
                or not surface_norm.startswith(reconstructed)
            ):
                kept.append(row)
                continue

            sibling_match = any(
                sibling.dulat.strip() == row.dulat.strip()
                and _pos_head(sibling.pos) == pos_head
                and (sibling.gloss or "").strip() == (row.gloss or "").strip()
                for sibling in clitic_rows
            )
            if sibling_match:
                continue
            kept.append(row)
        return kept
