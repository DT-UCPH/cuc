"""Deterministic nominal morphology completion and row splitting."""

from __future__ import annotations

from pathlib import Path

from morph_features.dulat_feature_reader import DulatFeatureReader
from morph_features.nominal_completion import NominalFeatureCompleter, rewrite_row
from morph_features.pos_renderer import render_pos
from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)


class NominalFeatureCompletionFixer(RefinementStep):
    """Complete nominal gender/number/state features from analysis and DULAT."""

    def __init__(self, dulat_db: Path) -> None:
        self._completer = NominalFeatureCompleter(DulatFeatureReader(db_path=dulat_db))

    @property
    def name(self) -> str:
        return "nominal-feature-completion"

    def refine_row(self, row: TabletRow) -> TabletRow:
        return rewrite_row(row, self._completer)

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        rows_processed = 0
        rows_changed = 0

        for raw in lines:
            if not raw.strip():
                out_lines.append(raw)
                continue
            if is_separator_line(raw):
                out_lines.append(normalize_separator_row(raw))
                continue

            row = parse_tsv_line(raw)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            if not self._is_nominal_row(row) or ";" in row.analysis or ";" in row.pos:
                out_lines.append(raw)
                continue

            variants = self._completer.complete_row(row)
            rewritten_rows = [
                TabletRow(
                    line_id=row.line_id,
                    surface=row.surface,
                    analysis=variant.analysis,
                    dulat=variant.dulat,
                    pos=render_pos(variant.features, fallback=row.pos),
                    gloss=variant.gloss,
                    comment=variant.comment,
                )
                for variant in variants
            ]
            rendered_lines = [item.to_tsv() for item in rewritten_rows]
            if len(rendered_lines) != 1 or rendered_lines[0] != raw:
                rows_changed += 1
            out_lines.extend(rendered_lines)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    @staticmethod
    def _is_nominal_row(row: TabletRow) -> bool:
        pos = row.pos or ""
        return pos.startswith("n.") or pos.startswith("adj.") or any(
            marker in pos for marker in ("DN", "PN", "RN", "TN", "GN", "MN")
        )
