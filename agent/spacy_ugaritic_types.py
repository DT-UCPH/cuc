"""Shared data structures for the spaCy-based Ugaritic rule spikes."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.steps.base import TabletRow


@dataclass(frozen=True)
class Candidate:
    """One candidate reading attached to a token."""

    analysis: str
    dulat: str
    pos: str
    gloss: str
    comment: str = ""

    @classmethod
    def from_row(cls, row: TabletRow) -> "Candidate":
        return cls(
            analysis=row.analysis,
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def to_row(self, *, line_id: str, surface: str) -> TabletRow:
        return TabletRow(
            line_id=line_id,
            surface=surface,
            analysis=self.analysis,
            dulat=self.dulat,
            pos=self.pos,
            gloss=self.gloss,
            comment=self.comment,
        )


@dataclass(frozen=True)
class GroupedToken:
    """One tablet token with all candidate rows grouped together."""

    line_id: str
    surface: str
    section_ref: str
    candidates: tuple[Candidate, ...]
