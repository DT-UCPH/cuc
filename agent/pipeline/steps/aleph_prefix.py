"""Fix bare ʔ in column 3 (analysis) that should be prefixed with '(' for reconstructed aleph.

Only applies within individual semicolon-separated analysis variants that are
NOT root-notation (/C-C-C/) and contain bare ʔ not already preceded by '('.
"""

import re

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow

# Match bare ʔ NOT preceded by '(' — i.e., ʔ that appears without reconstruction marker.
_BARE_ALEPH_RE = re.compile(r"(?<!\()ʔ")
_ALEPH_VOWELS = ("a", "i", "u")


class AlephPrefixFixer(RefinementStep):
    """Ensure every ʔ in analysis column is prefixed with '(' (reconstructed aleph marker)."""

    @property
    def name(self) -> str:
        return "aleph-prefix"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis = row.analysis
        if "ʔ" not in analysis:
            return row

        # Process each semicolon-separated variant independently
        variants = analysis.split(";")
        changed = False
        out_variants = []

        for var in variants:
            var = var.strip()
            fixed = self._fix_variant(var, surface=row.surface)
            if fixed != var:
                changed = True
            out_variants.append(fixed)

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

    def _fix_variant(self, var: str, surface: str) -> str:
        """Fix bare ʔ in a single analysis variant with reconstructable substitution."""
        # Skip root notation like /ʔ-b-d/
        if var.startswith("/") and var.endswith("/"):
            return var

        if not var or var == "ʔ":
            return var

        if not _BARE_ALEPH_RE.search(var):
            return var

        surface_norm = normalize_surface(surface)
        if not surface_norm:
            return var

        # Only keep substitutions that exactly reconstruct to the observed surface.
        for match in _BARE_ALEPH_RE.finditer(var):
            start = match.start()
            for vowel in _ALEPH_VOWELS:
                candidate = f"{var[:start]}(ʔ&{vowel}{var[start + 1 :]}"
                if normalize_surface(reconstruct_surface_from_analysis(candidate)) == surface_norm:
                    return candidate

        # No reconstructable substitution found.
        return var
