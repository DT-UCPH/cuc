"""Enforce assimilated nun encoding for prefixed N-stem verb analyses.

Conventions:
- Prefixed N-stem forms encode assimilated nun as `(]n]` after the
  preformative marker (e.g. `!t!(]n]ṯbr[`).
"""

from __future__ import annotations

import re

from pipeline.steps.base import RefinementStep, TabletRow

_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)
_VERBAL_NOUN_POS_RE = re.compile(r"\bvb\.\s*n\.", flags=re.IGNORECASE)
_POS_STEM_RE = re.compile(r"\b(Gpass|Dpass|Lpass|Špass|Gt|Dt|Lt|Nt|tD|tL|Št|G|D|L|N|R|Š)\b")
_PREFORMATIVE_RE = re.compile(
    r"^(?:![ytan](?:=+)?!|!\(ʔ&[aiu]!)",
    flags=re.IGNORECASE,
)
_CANONICAL_MARKER = "(]n]"
_LEGACY_MARKER = "](n]"
_REPEATED_N_WEAK_Y_RE = re.compile(r"^(?:(?:\(\]n\]|\]\(n\])\(y){2,}")
_REPEATED_N_MARKER_RE = re.compile(r"^(?:(?:\(\]n\]|\]\(n\])){2,}")


def _split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def _variant_value(values: list[str], index: int) -> str:
    if index < len(values):
        return values[index]
    if len(values) == 1:
        return values[0]
    return ""


def _pos_requires_n_assimilation(pos_text: str) -> bool:
    pos = (pos_text or "").strip()
    if not pos:
        return False
    if not _VB_POS_HEAD_RE.search(pos):
        return False
    if _VERBAL_NOUN_POS_RE.search(pos):
        return False
    stems = set(_POS_STEM_RE.findall(pos))
    return "N" in stems


def _insert_assimilated_n_marker(analysis: str) -> str:
    if not analysis or "[/" in analysis or "[" not in analysis:
        return analysis

    match = _PREFORMATIVE_RE.match(analysis)
    if match is None:
        return analysis

    prefix_end = match.end()
    tail = _normalize_assimilated_n_tail(analysis[prefix_end:])
    if not tail:
        return analysis

    if (
        tail.startswith(_CANONICAL_MARKER)
        or tail.startswith("]n]")
        or tail.startswith("(n")
        or tail.startswith("n")
    ):
        return f"{analysis[:prefix_end]}{tail}"

    return f"{analysis[:prefix_end]}{_CANONICAL_MARKER}{tail}"


def _normalize_assimilated_n_tail(tail: str) -> str:
    """Collapse legacy repeated N-markers to one canonical `(]n]` marker."""
    value = tail or ""
    value = _REPEATED_N_WEAK_Y_RE.sub(f"{_CANONICAL_MARKER}(y", value)
    value = _REPEATED_N_MARKER_RE.sub(_CANONICAL_MARKER, value)
    if value.startswith(_LEGACY_MARKER):
        value = _CANONICAL_MARKER + value[len(_LEGACY_MARKER) :]
    if value.startswith(f"(y{_LEGACY_MARKER}"):
        value = f"{_CANONICAL_MARKER}(y" + value[len(f"(y{_LEGACY_MARKER}") :]
    if value.startswith(f"(y{_CANONICAL_MARKER}"):
        value = f"{_CANONICAL_MARKER}(y" + value[len(f"(y{_CANONICAL_MARKER}") :]
    return value


def _strip_assimilated_n_marker(analysis: str) -> str:
    match = _PREFORMATIVE_RE.match(analysis or "")
    if match is None:
        return analysis
    prefix_end = match.end()
    tail = (analysis or "")[prefix_end:]
    for marker in (_CANONICAL_MARKER, "]n]", _LEGACY_MARKER):
        if tail.startswith(marker):
            return f"{analysis[:prefix_end]}{tail[len(marker) :]}"
    return analysis


class VerbNStemAssimilationFixer(RefinementStep):
    """Insert missing `(]n]` marker in prefixed N-stem analyses."""

    @property
    def name(self) -> str:
        return "verb-n-stem-assimilation"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis = (row.analysis or "").strip()
        if not analysis or "[" not in analysis:
            return row
        variants = _split_semicolon(analysis)
        if not variants:
            return row
        pos_variants = _split_semicolon(row.pos)

        changed = False
        out_variants: list[str] = []
        for idx, variant in enumerate(variants):
            pos_variant = _variant_value(pos_variants, idx)
            if _pos_requires_n_assimilation(pos_variant):
                updated = _insert_assimilated_n_marker(variant)
            else:
                updated = _strip_assimilated_n_marker(variant)
            if updated != variant:
                changed = True
            out_variants.append(updated)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(out_variants),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )
