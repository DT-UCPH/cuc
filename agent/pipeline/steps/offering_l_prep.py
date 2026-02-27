"""Disambiguate 'l' as preposition in offering-list sequences.

Pattern learned from sacrificial tablets:
    offering noun -> l -> recipient (DN/PN/TN/n.)

When an ambiguous row is encoded as:
    l(I);l(II);l(III) / l (I);l (II);l (III) / prep.;adv.;functor
and context matches offering-list syntax, normalize to:
    l(I) / l (I) / prep. / to
"""

from pathlib import Path

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    is_unresolved,
    parse_tsv_line,
)
from pipeline.steps.dulat_gate import LOOKUP_NORMALIZE

_OFFERING_SURFACES = {
    "gdlt",
    "alp",
    "alpm",
    "šnpt",
    "ʕr",
    "npš",
    "ššrt",
    "š",
    "ynt",
}


def _normalize(text: str) -> str:
    return (text or "").translate(LOOKUP_NORMALIZE).strip()


def _is_nominal_pos(pos_text: str) -> bool:
    p = (pos_text or "").strip()
    if not p:
        return False
    return any(tag in p for tag in ("n.", "adj.", "num.", "DN", "PN", "TN"))


class OfferingListLPrepFixer(RefinementStep):
    """Collapse ambiguous 'l' to preposition in offering-list context."""

    @property
    def name(self) -> str:
        return "offering-l-prep"

    def refine_row(self, row: TabletRow) -> TabletRow:
        # Context-aware logic is implemented in refine_file.
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

        prev_index: dict[int, int | None] = {}
        next_index: dict[int, int | None] = {}
        for order_idx, idx in enumerate(data_indexes):
            prev_index[idx] = data_indexes[order_idx - 1] if order_idx > 0 else None
            next_index[idx] = (
                data_indexes[order_idx + 1] if order_idx + 1 < len(data_indexes) else None
            )

        for idx, raw in enumerate(lines):
            row = parsed_by_index.get(idx)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            if is_unresolved(row):
                out_lines.append(raw)
                continue

            prev_row = parsed_by_index.get(prev_index.get(idx) or -1)
            next_row = parsed_by_index.get(next_index.get(idx) or -1)
            refined = self._refine_with_context(row=row, prev_row=prev_row, next_row=next_row)
            new_line = refined.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _refine_with_context(
        self, row: TabletRow, prev_row: TabletRow | None, next_row: TabletRow | None
    ) -> TabletRow:
        if not self._is_ambiguous_l_row(row):
            return row
        if prev_row is None or next_row is None:
            return row
        if not self._is_offering_row(prev_row):
            return row
        if not self._is_recipient_row(next_row):
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="l(I)",
            dulat="l (I)",
            pos="prep.",
            gloss="to",
            comment=row.comment,
        )

    def _is_ambiguous_l_row(self, row: TabletRow) -> bool:
        return (
            row.surface.strip() == "l"
            and row.analysis.strip() == "l(I);l(II);l(III)"
            and row.dulat.strip() == "l (I);l (II);l (III)"
            and row.pos.strip() == "prep.;adv.;functor"
            and row.gloss.strip() == "to;no;certainly"
        )

    def _is_offering_row(self, row: TabletRow) -> bool:
        surface = _normalize(row.surface)
        return surface in _OFFERING_SURFACES and _is_nominal_pos(row.pos)

    def _is_recipient_row(self, row: TabletRow) -> bool:
        pos_text = (row.pos or "").strip()
        if "vb" in pos_text:
            return False
        return _is_nominal_pos(pos_text)
