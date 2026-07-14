"""Builders for spaCy docs backed by tablet TSV rows."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal, Sequence

from spacy.language import Language
from spacy.tokens import Doc

from pipeline.config.l_negation_exception_refs import extract_separator_ref
from pipeline.steps.base import parse_tsv_line
from spacy_ugaritic.extensions import ensure_extensions
from spacy_ugaritic.types import Candidate, TabletToken

_EMPTY_TOKEN = "<EMPTY>"
_NAME_TAGS = ("DN", "PN", "RN", "TN", "GN", "MN")


def _candidate_classes(candidate: Candidate) -> set[str]:
    classes: set[str] = set()
    pos = candidate.pos or ""
    gloss = (candidate.gloss or "").lower()
    surface_hint = candidate.dulat or ""
    if "vb" in pos.lower():
        classes.add("VERB")
    if any(tag in pos for tag in _NAME_TAGS):
        classes.add("NAME")
    if "DN" in pos:
        classes.add("DN")
    if "PN" in pos:
        classes.add("PN")
    if "TN" in pos:
        classes.add("TN")
    if candidate.analysis == "kbd(I)/" and surface_hint == "kbd (I)":
        classes.add("KBD_COMPOUND")
    if gloss == "within":
        classes.add("BODY_COMPOUND")
    return classes


def token_classes(candidates: Sequence[Candidate]) -> frozenset[str]:
    classes: set[str] = set()
    for candidate in candidates:
        classes.update(_candidate_classes(candidate))
    return frozenset(classes)


def parse_grouped_tokens(lines: Iterable[str]) -> list[TabletToken]:
    tokens: list[TabletToken] = []
    active_ref = ""
    current_line_id = ""
    current_surface = ""
    current_ref = ""
    current_row_indexes: list[int] = []
    current_candidates: list[Candidate] = []

    def flush() -> None:
        nonlocal current_line_id, current_surface, current_ref
        nonlocal current_row_indexes, current_candidates
        if not current_candidates or not current_surface:
            current_line_id = ""
            current_surface = ""
            current_ref = ""
            current_row_indexes = []
            current_candidates = []
            return
        tokens.append(
            TabletToken(
                line_id=current_line_id,
                surface=current_surface,
                section_ref=current_ref,
                row_indexes=tuple(current_row_indexes),
                candidates=tuple(current_candidates),
            )
        )
        current_line_id = ""
        current_surface = ""
        current_ref = ""
        current_row_indexes = []
        current_candidates = []

    for row_index, raw in enumerate(lines):
        separator_ref = extract_separator_ref(raw)
        if separator_ref is not None:
            flush()
            active_ref = separator_ref
            continue
        row = parse_tsv_line(raw)
        if row is None:
            flush()
            continue
        key = (row.line_id.strip(), row.surface.strip())
        current_key = (current_line_id, current_surface)
        if current_candidates and key != current_key:
            flush()
        if not current_candidates:
            current_line_id = key[0]
            current_surface = key[1]
            current_ref = active_ref
        current_row_indexes.append(row_index)
        current_candidates.append(Candidate.from_row(row))

    flush()
    return tokens


def parse_row_tokens(lines: Iterable[str]) -> list[TabletToken]:
    tokens: list[TabletToken] = []
    active_ref = ""
    for row_index, raw in enumerate(lines):
        separator_ref = extract_separator_ref(raw)
        if separator_ref is not None:
            active_ref = separator_ref
            continue
        row = parse_tsv_line(raw)
        if row is None:
            continue
        tokens.append(
            TabletToken(
                line_id=row.line_id.strip(),
                surface=row.surface.strip(),
                section_ref=active_ref,
                row_indexes=(row_index,),
                candidates=(Candidate.from_row(row),),
            )
        )
    return tokens


def build_doc(nlp: Language, tokens: Sequence[TabletToken], *, source_name: str = "") -> Doc:
    ensure_extensions()
    words = [token.surface or _EMPTY_TOKEN for token in tokens]
    spaces = [True] * len(words)
    if spaces:
        spaces[-1] = False
    doc = Doc(nlp.vocab, words=words, spaces=spaces)
    doc._.source_name = source_name
    for spacy_token, tablet_token in zip(doc, tokens, strict=True):
        spacy_token._.line_id = tablet_token.line_id
        spacy_token._.surface = tablet_token.surface
        spacy_token._.section_ref = tablet_token.section_ref
        spacy_token._.row_indexes = tablet_token.row_indexes
        spacy_token._.candidates = tablet_token.candidates
        spacy_token._.resolved_candidates = tablet_token.candidates
        spacy_token._.coarse_classes = token_classes(tablet_token.candidates)
    return doc


def build_doc_from_path(
    nlp: Language,
    path: Path,
    *,
    mode: Literal["grouped", "row"] = "grouped",
) -> Doc:
    lines = path.read_text(encoding="utf-8").splitlines()
    tokens = parse_grouped_tokens(lines) if mode == "grouped" else parse_row_tokens(lines)
    return build_doc(nlp, tokens, source_name=path.name)


# Transitional alias for existing grouped-token tests and scripts.
group_tablet_lines = parse_grouped_tokens
