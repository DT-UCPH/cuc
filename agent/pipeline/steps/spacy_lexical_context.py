"""Integrated spaCy-backed replacements for lexical-context refinement steps."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import RefinementStep, StepResult
from spacy_ugaritic.doc_builder import build_doc, parse_grouped_tokens, parse_row_tokens
from spacy_ugaritic.language import (
    create_ugaritic_baal_context_nlp,
    create_ugaritic_ydk_context_nlp,
)
from spacy_ugaritic.rewriter import count_data_rows, render_resolved_lines


class _BaseSpacyLexicalContextDisambiguator(RefinementStep):
    def refine_row(self, row):  # pragma: no cover - file-level step
        return row


class SpacyBaalContextDisambiguator(_BaseSpacyLexicalContextDisambiguator):
    """Apply bʕl lexical-context disambiguation at the historical pre-l stage."""

    def __init__(self) -> None:
        self._nlp = create_ugaritic_baal_context_nlp()

    @property
    def name(self) -> str:
        return "spacy-baal-context"

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        tokens = parse_row_tokens(lines)
        rows_processed = count_data_rows(lines)
        if not tokens:
            return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=0)

        doc = build_doc(self._nlp, tokens, source_name=path.name)
        resolved_doc = self._nlp(doc)
        out_lines, rows_changed = render_resolved_lines(lines, tokens, resolved_doc)
        if rows_changed:
            path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)


class SpacyYdkContextDisambiguator(_BaseSpacyLexicalContextDisambiguator):
    """Apply `ydk` lexical-context disambiguation at the historical post-k stage."""

    def __init__(self) -> None:
        self._nlp = create_ugaritic_ydk_context_nlp()

    @property
    def name(self) -> str:
        return "spacy-ydk-context"

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        tokens = parse_grouped_tokens(lines)
        rows_processed = count_data_rows(lines)
        if not tokens:
            return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=0)

        doc = build_doc(self._nlp, tokens, source_name=path.name)
        resolved_doc = self._nlp(doc)
        out_lines, rows_changed = render_resolved_lines(lines, tokens, resolved_doc)
        if rows_changed:
            path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)
