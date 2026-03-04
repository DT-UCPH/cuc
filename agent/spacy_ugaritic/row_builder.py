"""Builders for spaCy docs backed by row-level tablet TSV lines."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from spacy.language import Language
from spacy.tokens import Doc

from pipeline.steps.base import TabletRow, parse_tsv_line
from spacy_ugaritic.extensions import ensure_extensions

_EMPTY_ROW_TOKEN = "<EMPTY>"


def build_row_doc(
    nlp: Language, rows: list[tuple[int, TabletRow]], *, source_name: str = ""
) -> Doc:
    """Build a spaCy doc with one token per TSV data row."""
    ensure_extensions()
    words = [row.surface or _EMPTY_ROW_TOKEN for _, row in rows]
    spaces = [True] * len(words)
    if spaces:
        spaces[-1] = False
    doc = Doc(nlp.vocab, words=words, spaces=spaces)
    doc._.source_name = source_name
    for token, (line_index, row) in zip(doc, rows, strict=True):
        token._.line_index = line_index
        token._.row = row
        token._.resolved_row = row
    return doc


def parse_rows(lines: Iterable[str]) -> list[tuple[int, TabletRow]]:
    """Return parseable TSV data rows with their original line indexes."""
    rows: list[tuple[int, TabletRow]] = []
    for line_index, raw in enumerate(lines):
        row = parse_tsv_line(raw)
        if row is None:
            continue
        rows.append((line_index, row))
    return rows


def build_row_doc_from_path(nlp: Language, path: Path) -> Doc:
    """Build a row-level doc from a TSV path."""
    rows = parse_rows(path.read_text(encoding="utf-8").splitlines())
    return build_row_doc(nlp, rows, source_name=path.name)
