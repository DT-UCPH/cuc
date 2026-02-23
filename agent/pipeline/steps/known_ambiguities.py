"""Preserve known multi-option ambiguities for contextual disambiguation."""

from dataclasses import dataclass
from typing import Iterable, Tuple

from pipeline.steps.base import RefinementStep, TabletRow


@dataclass(frozen=True)
class AmbiguityPayload:
    """Aligned col3-col6 payload for one known ambiguous surface."""

    analysis: str
    dulat: str
    pos: str
    gloss: str


@dataclass(frozen=True)
class AmbiguityRule:
    """Rule matching a surface (optionally constrained by DULAT/gloss hints)."""

    surface: str
    payload: AmbiguityPayload
    dulat_hint: str = ""
    gloss_hint: str = ""

    def matches(self, row: TabletRow) -> bool:
        if row.surface.strip() != self.surface:
            return False
        if self.dulat_hint and self.dulat_hint not in row.dulat:
            return False
        if self.gloss_hint and self.gloss_hint not in row.gloss:
            return False
        return True


class KnownAmbiguityExpander(RefinementStep):
    """Expand selected high-value lexemes to full ambiguity sets."""

    def __init__(self, rules: Iterable[AmbiguityRule] | None = None) -> None:
        self._rules: Tuple[AmbiguityRule, ...] = tuple(rules or _DEFAULT_RULES)

    @property
    def name(self) -> str:
        return "known-ambiguity-expander"

    def refine_row(self, row: TabletRow) -> TabletRow:
        for rule in self._rules:
            if not rule.matches(row):
                continue
            payload = rule.payload
            if (
                row.analysis == payload.analysis
                and row.dulat == payload.dulat
                and row.pos == payload.pos
                and row.gloss == payload.gloss
            ):
                return row
            return TabletRow(
                line_id=row.line_id,
                surface=row.surface,
                analysis=payload.analysis,
                dulat=payload.dulat,
                pos=payload.pos,
                gloss=payload.gloss,
                comment=row.comment,
            )
        return row


_DEFAULT_RULES: Tuple[AmbiguityRule, ...] = (
    AmbiguityRule(
        surface="ydk",
        payload=AmbiguityPayload(
            analysis="yd(I)/+k;yd(I)/+k=;yd(II)/+k;yd(II)/+k=;!y!dk[;!y=!dk[",
            dulat="yd (I), -k (I);yd (I), -k (I);yd (II), -k (I);yd (II), -k (I);d-k(-k)/;d-k(-k)/",
            pos="n. f.,pers. pn.;n. f.,pers. pn.;n. m.,pers. pn.;n. m.,pers. pn.;vb;vb",
            gloss=(
                "hand, your(s);hand, your(s);love, your(s);love, your(s);"
                "to be pounded;to be pounded"
            ),
        ),
    ),
    AmbiguityRule(
        surface="šlmm",
        dulat_hint="šlm (II)",
        payload=AmbiguityPayload(
            analysis="šlm(II)/~m;šlm(II)/m",
            dulat="šlm (II);šlm (II)",
            pos="n. m.;n. m.",
            gloss="communion victim / sacrifice;communion victim / sacrifice",
        ),
    ),
)
