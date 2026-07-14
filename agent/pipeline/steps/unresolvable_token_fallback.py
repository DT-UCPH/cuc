"""Convert tokens with no reconstructable analysis left into '?' + hint.

Runs at the very end of the refinement pipeline, after every repair step
(plural split, suffix clitics, weak preformatives, stem fixers) has had its
chance: rendering intentionally emits repairable baselines, so gating any
earlier rejects healthy tokens (regression: ilm, yqḥ, bˤlny, ˤbdk). What
still cannot reconstruct here (yddll -> dll[:d) is replaced by an
unresolved row that preserves the DULAT candidates as a comment hint.
"""

from pathlib import Path
from typing import List, Tuple

from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line
from pipeline.steps.variant_reconstruction_pruner import _row_is_protected, _row_reconstructs

_HINT_PREFIX = "DULAT candidates (no reconstructable encoding): "
_MAX_HINTED_CANDIDATES = 3


def _group_hint(rows: List[TabletRow]) -> str:
    hints = []
    for row in rows[:_MAX_HINTED_CANDIDATES]:
        label = " - ".join(part for part in (row.dulat.strip(), row.gloss.strip()) if part)
        if label and label not in hints:
            hints.append(label)
    return "; ".join(hints)


class UnresolvableTokenFallback(RefinementStep):
    """Replaces fully non-reconstructable token groups with '?' + hint."""

    @property
    def name(self) -> str:
        return "unresolvable-token-fallback"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()

        parsed: List[Tuple[int, TabletRow]] = []
        for idx, raw in enumerate(lines):
            if raw.lstrip().startswith("#"):
                continue
            row = parse_tsv_line(raw)
            if row is not None:
                parsed.append((idx, row))

        rows_changed = 0
        drop_lines: set = set()
        replacements: dict = {}
        group: List[Tuple[int, TabletRow]] = []

        def _flush() -> None:
            nonlocal rows_changed
            if not group:
                return
            first = group[0][1]
            surface = first.surface.strip()
            if not surface or "x" in surface.lower():
                return
            rows = [row for _i, row in group]
            if any(_row_is_protected(row) for row in rows):
                return
            if any(_row_reconstructs(row) for row in rows):
                return
            hint = _group_hint(rows)
            if not hint:
                return
            fallback = TabletRow(
                line_id=first.line_id,
                surface=first.surface,
                analysis="?",
                dulat="?",
                pos="?",
                gloss="?",
                comment=_HINT_PREFIX + hint,
            )
            replacements[group[0][0]] = fallback.to_tsv()
            for idx, _row in group[1:]:
                drop_lines.add(idx)
            rows_changed += len(group)

        for idx, row in parsed:
            if group and row.line_id != group[0][1].line_id:
                _flush()
                group = []
            group.append((idx, row))
        _flush()

        if not rows_changed:
            return StepResult(file=path.name, rows_processed=len(parsed), rows_changed=0)

        out_lines = []
        for idx, raw in enumerate(lines):
            if idx in drop_lines:
                continue
            out_lines.append(replacements.get(idx, raw))
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=len(parsed), rows_changed=rows_changed)
