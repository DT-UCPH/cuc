"""Normalize weak-final finite SC forms ending in surface -t.

For weak-final verbs (/...-...-y/ or /...-...-w/), finite forms with surface
final ``t`` should encode suffix-conjugation ending as ``[t``.
"""

import re
from typing import Optional, Tuple

from pipeline.steps.base import RefinementStep, TabletRow

_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_PREFORMATIVE_RE = re.compile(r"![ytan](?:=|==|===)?!")


class WeakFinalSuffixConjugationFixer(RefinementStep):
    """Rewrite weak-final finite verb analyses from ``[`` to ``[t`` when needed."""

    @property
    def name(self) -> str:
        return "weak-final-sc"

    def refine_row(self, row: TabletRow) -> TabletRow:
        surface = row.surface.strip()
        analysis = row.analysis.strip()
        dulat = row.dulat.strip()
        pos = row.pos.strip()

        if not surface or not analysis or not dulat or not pos:
            return row
        if not surface.endswith("t"):
            return row
        if "[" not in analysis:
            return row

        variants = [v.strip() for v in analysis.split(";")]
        dulat_variants = [v.strip() for v in dulat.split(";")]
        pos_variants = [v.strip() for v in pos.split(";")]

        changed = False
        out_variants = []
        for idx, var in enumerate(variants):
            dulat_var = dulat_variants[idx] if idx < len(dulat_variants) else ""
            pos_var = pos_variants[idx] if idx < len(pos_variants) else ""
            new_var = self._fix_variant(var=var, dulat_var=dulat_var, pos_var=pos_var)
            if new_var != var:
                changed = True
            out_variants.append(new_var)

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

    def _fix_variant(self, var: str, dulat_var: str, pos_var: str) -> str:
        if "vb" not in pos_var:
            return var
        if "[" not in var or "/" in var:
            return var
        if "[t" in var:
            return var
        if _PREFORMATIVE_RE.search(var):
            return var

        radicals = _variant_root_radicals(dulat_var)
        if radicals is None:
            return var
        first, second, third = radicals
        if third not in {"y", "w"}:
            return var
        if second == "t":
            return var

        return var.replace("[", "[t", 1)


def _variant_root_radicals(dulat_var: str) -> Optional[Tuple[str, str, str]]:
    """Extract /C-C-C/ radicals from a DULAT root token in one variant."""
    token = (dulat_var or "").strip()
    if not token:
        return None

    # Keep only the first CSV token in this variant.
    if "," in token:
        token = token.split(",", 1)[0].strip()

    # Accept forms like '/k-l-y/' or '/k-l-y/ (I)'.
    m = re.match(r"^/([^/]+)/", token)
    if not m:
        return None
    core = m.group(1)
    parts = [p.strip() for p in core.split("-") if p.strip()]
    if len(parts) != 3:
        return None
    if not all(_LETTER_RE.search(p) for p in parts):
        return None
    return parts[0], parts[1], parts[2]
