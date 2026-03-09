"""Fix weak-initial verb forms in analysis variants.

For weak-initial verbs in prefix conjugation, analysis should encode:
- prefix preformative in ``!...!``
- hidden initial radical as ``(y`` or ``(l`` immediately after that marker

For attested forms where the initial weak radical drops from the written
surface entirely, the analysis should encode it as reconstructed, e.g.
``qḥ -> !!(lqḥ[`` for ``/l-q-ḥ/`` imperatives.
"""

import re

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow

_PREFORMATIVES = {"t", "y", "a", "n", "i", "u"}
_WEAK_INITIAL_RE = re.compile(r"^\s*/(?P<radical>[yl])-")
_PREFORMATIVE_MARKER_RE = re.compile(
    r"^(?:!(?P<plain>[ytaniu])(?:=|==|===)?!|!\(ʔ&(?P<aleph>[aiu])!)"
)
_ASSIMILATED_N_MARKER = "(]n]"


def _format_preformative_marker(letter: str) -> str:
    """Render canonical prefix-conjugation marker for one preformative letter."""
    preformative = (letter or "").strip()
    if preformative in {"a", "i", "u"}:
        return f"!(ʔ&{preformative}!"
    return f"!{preformative}!"


def _surface_matches(surface: str, analysis: str) -> bool:
    return normalize_surface(reconstruct_surface_from_analysis(analysis)) == normalize_surface(
        surface
    )


class WeakVerbFixer(RefinementStep):
    """Normalize weak-initial prefix and dropped-radical verb forms."""

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
        if "vb" not in pos:
            return row
        if "[" not in analysis:
            return row

        roots = [value.strip() for value in dulat.split(";")]
        pos_variants = [value.strip() for value in pos.split(";")]
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
        """Fix one analysis variant if it is a weak-initial verbal form."""
        if "vb" not in pos_var:
            return var
        if "[" not in var:
            return var

        root_match = _WEAK_INITIAL_RE.match(dulat_var)
        if root_match is None:
            return var
        radical = root_match.group("radical")

        marked = self._normalize_marked_variant(var, radical=radical, surface=surface)
        if marked != var:
            return marked
        return self._normalize_unmarked_variant(
            var,
            radical=radical,
            surface=surface,
        )

    def _normalize_marked_variant(self, var: str, *, radical: str, surface: str) -> str:
        """Ensure marked weak-initial variants reconstruct the hidden radical."""
        match = _PREFORMATIVE_MARKER_RE.match(var)
        if match is None:
            return var

        prefix_marker = match.group(0)
        remainder = var[match.end() :]
        n_marker = ""
        if remainder.startswith(_ASSIMILATED_N_MARKER):
            n_marker = _ASSIMILATED_N_MARKER
            remainder = remainder[len(_ASSIMILATED_N_MARKER) :]

        if remainder.startswith(f"({radical}"):
            return var
        if remainder.startswith(radical):
            remainder = f"({radical}" + remainder[1:]
        else:
            remainder = f"({radical}" + remainder

        candidate = prefix_marker + n_marker + remainder
        if _surface_matches(surface, candidate):
            return candidate
        return var

    def _normalize_unmarked_variant(
        self,
        var: str,
        *,
        radical: str,
        surface: str,
    ) -> str:
        """Add missing prefix/radical markers for weak-initial forms."""
        if not surface:
            return var
        if radical == "l" and var.startswith("(l") and not var.startswith("!!"):
            candidate = f"!!{var}"
            if _surface_matches(surface, candidate):
                return candidate

        if surface[0] in _PREFORMATIVES:
            prefix = surface[0]
            if radical == "y":
                if not var.startswith(prefix):
                    return var
                candidate = f"{_format_preformative_marker(prefix)}(y{var[1:]}"
            else:
                if not var.startswith(radical):
                    return var
                candidate = f"{_format_preformative_marker(prefix)}({radical}{var[1:]}"
            if _surface_matches(surface, candidate):
                return candidate
            return var

        if radical != "l" or not var.startswith("l"):
            return var
        candidate = f"!!(l{var[1:]}"
        if _surface_matches(surface, candidate):
            return candidate
        return var
