"""Fix weak-initial /y-/ prefix forms in analysis variants.

For weak-initial verbs in prefix conjugation, analysis should encode:
- prefix preformative in ``!...!``
- hidden initial radical as ``(y`` immediately after that marker.
"""

import re

from pipeline.steps.base import RefinementStep, TabletRow

# Preformative consonants for prefix conjugation
_PREFORMATIVES = {"t", "y", "a", "n", "i"}

_WEAK_INITIAL_Y_RE = re.compile(r"^\s*/y-")
_PREFORMATIVE_MARKER_RE = re.compile(r"^!([ytani])(?:=|==|===)?!")


class WeakVerbFixer(RefinementStep):
    """Normalize weak-initial /y-/ prefix forms."""

    @property
    def name(self) -> str:
        return "weak-verb"

    def refine_row(self, row: TabletRow) -> TabletRow:
        surface = row.surface.strip()
        analysis = row.analysis.strip()
        dulat = row.dulat.strip()
        pos = row.pos.strip()

        if not surface or not analysis or not dulat or not pos:
            return row

        # Only verbs
        if "vb" not in pos:
            return row

        # Must be a verb form (has '[' ending)
        if "[" not in analysis:
            return row

        # Check DULAT for root pattern /C-C-C/
        roots = [v.strip() for v in dulat.split(";")]
        pos_variants = [v.strip() for v in pos.split(";")]

        variants = analysis.split(";")
        changed = False
        out = []

        for idx, var in enumerate(variants):
            var = var.strip()
            d_var = roots[idx].strip() if idx < len(roots) else ""
            p_var = pos_variants[idx].strip() if idx < len(pos_variants) else ""

            new_var = self._fix_variant(var, d_var, p_var, surface)
            if new_var != var:
                changed = True
            out.append(new_var)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(out),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _fix_variant(self, var: str, dulat_var: str, pos_var: str, surface: str) -> str:
        """Fix one analysis variant if it is weak-initial /y-/ prefix form."""
        if "vb" not in pos_var:
            return var
        if "[" not in var:
            return var

        if not _WEAK_INITIAL_Y_RE.match(dulat_var):
            return var

        marked = self._normalize_marked_variant(var)
        if marked != var:
            return marked

        return self._normalize_unmarked_variant(var, surface)

    def _normalize_marked_variant(self, var: str) -> str:
        """Ensure weak-initial marked variant has '(y' after !preformative!."""
        m = _PREFORMATIVE_MARKER_RE.match(var)
        if not m:
            return var

        prefix_marker = m.group(0)
        remainder = var[m.end() :]
        if remainder.startswith("(y"):
            return var
        if remainder.startswith("y"):
            remainder = "(y" + remainder[1:]
        else:
            remainder = "(y" + remainder
        return prefix_marker + remainder

    def _normalize_unmarked_variant(self, var: str, surface: str) -> str:
        """Add !preformative! and '(y' for unmarked weak-initial prefix forms."""
        if not surface or surface[0] not in _PREFORMATIVES:
            return var
        prefix = surface[0]
        if not var.startswith(prefix):
            return var
        return f"!{prefix}!(y{var[1:]}"
