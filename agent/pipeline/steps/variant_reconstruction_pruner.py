"""Drop variant rows that cannot reconstruct their surface.

Cross-token leakage occasionally attaches a foreign analysis to a token
(`gh -> ytn[`). Such rows are detectable mechanically: their analysis does
not reconstruct to the row surface while a sibling variant of the same token
does. Pruning is conservative: a token must keep at least one row, unresolved
``?`` rows and MERGE-annotated rows are never dropped, and damaged surfaces
(containing broken-sign ``x``) are left untouched.
"""

from pathlib import Path
from typing import List, Tuple

from linter.lint import (
    ANALYSIS_SURFACE_LETTER_RE,
    normalize_surface,
    reconstruct_surface_from_analysis,
)
from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line

_MERGE_MARKER = "MERGE WITH THE"


def _expected_surface(surface: str) -> str:
    letters = "".join(ch for ch in surface if ANALYSIS_SURFACE_LETTER_RE.match(ch))
    return normalize_surface(letters or surface)


def _row_reconstructs(row: TabletRow) -> bool:
    analysis = (row.analysis or "").strip()
    if not analysis or analysis == "?":
        return False
    reconstructed = normalize_surface(reconstruct_surface_from_analysis(analysis))
    return reconstructed == _expected_surface(row.surface.strip())


def _row_is_protected(row: TabletRow) -> bool:
    if (row.analysis or "").strip() in {"", "?"}:
        return True
    return _MERGE_MARKER in (row.comment or "")


class VariantReconstructionPruner(RefinementStep):
    """Removes parser-artifact variants shadowing a reconstructable sibling."""

    @property
    def name(self) -> str:
        return "variant-reconstruction-pruner"

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

        drop_lines: set = set()
        group: List[Tuple[int, TabletRow]] = []

        def _flush() -> None:
            if len(group) < 2:
                return
            surface = group[0][1].surface.strip()
            if "x" in surface.lower():
                return
            healthy = [
                (idx, row)
                for idx, row in group
                if not _row_is_protected(row) and _row_reconstructs(row)
            ]
            if not healthy:
                return
            for idx, row in group:
                if _row_is_protected(row) or _row_reconstructs(row):
                    continue
                drop_lines.add(idx)

        for idx, row in parsed:
            if group and row.line_id != group[0][1].line_id:
                _flush()
                group = []
            group.append((idx, row))
        _flush()

        if not drop_lines:
            return StepResult(file=path.name, rows_processed=len(parsed), rows_changed=0)

        out_lines = [raw for idx, raw in enumerate(lines) if idx not in drop_lines]
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=len(parsed), rows_changed=len(drop_lines))
