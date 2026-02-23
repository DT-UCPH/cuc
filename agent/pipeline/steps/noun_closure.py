"""Fix noun/adjective analyses that lack the required trailing '/' closure marker."""

from pipeline.steps.base import RefinementStep, TabletRow

# POS labels that require '/' closure in analysis column
_NOUN_POS_PREFIXES = {"n.", "adj.", "DN", "TN", "PN", "GN", "RN", "num."}


def _is_noun_like_pos(pos: str) -> bool:
    """Check if the POS field contains only noun-like tags (all variants must be noun-like)."""
    if not pos.strip():
        return False
    variants = [v.strip() for v in pos.split(";")]
    for v in variants:
        slots = [s.strip() for s in v.split(",")]
        first = slots[0] if slots else ""
        if not any(first.startswith(prefix) for prefix in _NOUN_POS_PREFIXES):
            return False
    return True


def _analysis_needs_closure(analysis: str) -> bool:
    """Check if analysis token lacks '/' and is not a verb form (no '[')."""
    if "/" in analysis or "[" in analysis:
        return False
    # Don't touch analysis-only tokens like particles, prepositions
    return True


class NounPosClosureFixer(RefinementStep):
    """Append '/' to noun/adjective analyses that lack it."""

    @property
    def name(self) -> str:
        return "noun-pos-closure"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if not _is_noun_like_pos(row.pos):
            return row

        analysis = row.analysis
        if not analysis:
            return row

        # Process each semicolon-separated variant
        variants = analysis.split(";")
        changed = False
        out_variants = []
        pos_variants = [v.strip() for v in row.pos.split(";")]

        for idx, var in enumerate(variants):
            var = var.strip()
            pos_v = pos_variants[idx].strip() if idx < len(pos_variants) else ""

            # Only fix noun-like POS variants
            first_slot = pos_v.split(",")[0].strip() if pos_v else ""
            is_noun = any(first_slot.startswith(p) for p in _NOUN_POS_PREFIXES)

            if is_noun and _analysis_needs_closure(var):
                var = var + "/"
                changed = True
            out_variants.append(var)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(out_variants),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )
