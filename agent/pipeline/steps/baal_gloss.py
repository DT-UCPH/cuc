"""Normalize `bʕl (II)` glosses once POS has been disambiguated."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep, TabletRow

_BAAL_DULAT = "bʕl (II)"
_BAAL_DN_GLOSS = "Baʿlu/Baal"
_BAAL_NOUN_GLOSS = "lord"


class BaalGlossFixer(RefinementStep):
    """Keep Baal glosses aligned with resolved DN vs noun POS."""

    @property
    def name(self) -> str:
        return "baal-gloss"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if row.dulat.strip() != _BAAL_DULAT:
            return row
        pos = row.pos.strip()
        if "DN" in pos and "n." not in pos:
            target_gloss = _BAAL_DN_GLOSS
        elif "n." in pos and "DN" not in pos:
            target_gloss = _BAAL_NOUN_GLOSS
        else:
            return row
        if row.gloss.strip() == target_gloss:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=row.analysis,
            dulat=row.dulat,
            pos=row.pos,
            gloss=target_gloss,
            comment=row.comment,
        )
