"""Integrated spaCy-backed replacement for the legacy offering `l` step."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import RefinementStep, StepResult
from spacy_ugaritic.language import create_ugaritic_offering_context_nlp
from spacy_ugaritic.row_builder import build_row_doc, parse_rows
from spacy_ugaritic.row_rewriter import count_data_rows, render_resolved_rows


class SpacyOfferingContextDisambiguator(RefinementStep):
    """Apply offering-list `l` normalization in one row-level pass."""

    def __init__(self) -> None:
        self._nlp = create_ugaritic_offering_context_nlp()

    @property
    def name(self) -> str:
        return "spacy-offering-context"

    def refine_row(self, row):  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        rows = parse_rows(lines)
        rows_processed = count_data_rows(lines)
        if not rows:
            return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=0)

        doc = build_row_doc(self._nlp, rows, source_name=path.name)
        resolved_doc = self._nlp(doc)
        out_lines, rows_changed = render_resolved_rows(lines, resolved_doc)
        if rows_changed:
            path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)
