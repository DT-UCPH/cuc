"""Integrated spaCy-backed replacement for the legacy `k` context step."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import RefinementStep, StepResult
from spacy_ugaritic.doc_builder import build_doc, group_tablet_lines
from spacy_ugaritic.language import create_ugaritic_k_context_nlp
from spacy_ugaritic.rewriter import count_data_rows, render_resolved_lines


class SpacyKContextDisambiguator(RefinementStep):
    """Apply `k`-context disambiguation in one document-level pass."""

    def __init__(self) -> None:
        self._nlp = create_ugaritic_k_context_nlp()

    @property
    def name(self) -> str:
        return "spacy-k-context"

    def refine_row(self, row):  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        grouped_tokens = group_tablet_lines(lines)
        rows_processed = count_data_rows(lines)
        if not grouped_tokens:
            return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=0)

        doc = build_doc(self._nlp, grouped_tokens, source_name=path.name)
        resolved_doc = self._nlp(doc)
        out_lines, rows_changed = render_resolved_lines(lines, grouped_tokens, resolved_doc)
        if rows_changed:
            path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)
