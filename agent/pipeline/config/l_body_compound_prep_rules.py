"""Canonical payload rules for `l + body-part` compound prepositions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LBodyCompoundPrepRule:
    second_analysis: str
    second_dulat: str
    second_pos: str
    second_gloss: str


L_BODY_COMPOUND_PREP_RULES = {
    "pˤn": LBodyCompoundPrepRule(
        second_analysis="pˤn/",
        second_dulat="pʕn",
        second_pos="n. f.",
        second_gloss="at the feet of",
    ),
    "ẓr": LBodyCompoundPrepRule(
        second_analysis="ẓr(I)/",
        second_dulat="ẓr (I)",
        second_pos="n. m.",
        second_gloss="upon",
    ),
}
