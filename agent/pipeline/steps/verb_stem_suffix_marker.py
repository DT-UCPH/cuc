"""Enforce verbal stem suffix markers in analysis based on POS stems.

Conventions:
- D / Dt / tD -> `:d`
- L / Lt / tL -> `:l`
- R -> `:r`
- *pass stems -> `:pass`
"""

from __future__ import annotations

import re

from pipeline.steps.base import RefinementStep, TabletRow

_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)
_VERBAL_NOUN_POS_RE = re.compile(r"\bvb\.\s*n\.", flags=re.IGNORECASE)
_POS_STEM_RE = re.compile(r"\b(Gpass|Dpass|Lpass|Špass|Gt|Dt|Lt|Nt|tD|tL|Št|G|D|L|N|R|Š)\b")


def _required_markers_from_pos(pos_text: str) -> tuple[str, ...]:
    pos = (pos_text or "").strip()
    if not pos:
        return tuple()
    if not _VB_POS_HEAD_RE.search(pos):
        return tuple()
    if _VERBAL_NOUN_POS_RE.search(pos):
        return tuple()

    stems = set(_POS_STEM_RE.findall(pos))
    markers: list[str] = []
    if stems & {"D", "Dt", "tD"}:
        markers.append(":d")
    if stems & {"L", "Lt", "tL"}:
        markers.append(":l")
    if "R" in stems:
        markers.append(":r")
    if stems & {"Gpass", "Dpass", "Lpass", "Špass"}:
        markers.append(":pass")
    return tuple(markers)


def _insert_marker(analysis: str, marker: str) -> str:
    if marker in analysis:
        return analysis
    if "[" not in analysis:
        return analysis

    head, tail = analysis.split("[", 1)
    if not head:
        return analysis

    clitic_start = len(tail)
    for ch in ("+", "~"):
        idx = tail.find(ch)
        if idx >= 0:
            clitic_start = min(clitic_start, idx)

    return f"{head}[{tail[:clitic_start]}{marker}{tail[clitic_start:]}"


class VerbStemSuffixMarkerFixer(RefinementStep):
    """Append missing `:d/:l/:r/:pass` markers required by POS stem labels."""

    @property
    def name(self) -> str:
        return "verb-stem-suffix-marker"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis = (row.analysis or "").strip()
        if not analysis or "[" not in analysis:
            return row
        if "[/" in analysis:
            return row

        markers = _required_markers_from_pos(row.pos or "")
        if not markers:
            return row

        updated = analysis
        for marker in markers:
            updated = _insert_marker(updated, marker)
        if updated == analysis:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=updated,
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )
