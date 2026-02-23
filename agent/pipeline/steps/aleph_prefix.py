"""Fix bare ʔ in column 3 (analysis) that should be prefixed with '(' for reconstructed aleph.

Only applies within individual semicolon-separated analysis variants that are
NOT root-notation (/C-C-C/) and contain bare ʔ not already preceded by '('.
"""

import re

from pipeline.steps.base import RefinementStep, TabletRow

# Match bare ʔ NOT preceded by '(' — i.e., ʔ that appears without reconstruction marker.
_BARE_ALEPH_RE = re.compile(r"(?<!\()ʔ")


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
            fixed = self._fix_variant(var)
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

    def _fix_variant(self, var: str) -> str:
        """Fix bare ʔ in a single analysis variant."""
        # Skip root notation like /ʔ-b-d/
        if var.startswith("/") and var.endswith("/"):
            return var

        # Skip if variant is just a reference (no letter content besides ʔ)
        if not var or var == "ʔ":
            return var

        # Only fix variants that are noun-like (ending in /) — verb variants with [
        # already handled by other fixers
        if "[" in var:
            # For verb forms, only fix ʔ that is clearly inside the stem, not the root ref
            return _BARE_ALEPH_RE.sub("(ʔ", var)

        if "/" in var:
            # Noun variant — fix bare ʔ
            return _BARE_ALEPH_RE.sub("(ʔ", var)

        # For variants without / or [ (particles, etc.), be conservative — skip
        return var
