"""Normalize mixed bˤlm ambiguity in god-list style rows.

When `bˤlm` is encoded as two variants:
- `bˤl(II)/` (n. m./DN)
- `bˤl(I)/m` (labourer plural)
the preferred normalization is a single plural noun reading:
- `bˤl(II)/m` -> `bʕl (II)` -> `n. m.` -> `lord`
"""

from pipeline.steps.base import RefinementStep, TabletRow


class BaalPluralGodListFixer(RefinementStep):
    """Collapse mixed bˤlm ambiguity to the noun plural lord reading."""

    @property
    def name(self) -> str:
        return "baal-plural"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if row.surface.strip() != "bˤlm":
            return row

        analysis_variants = [v.strip() for v in row.analysis.split(";") if v.strip()]
        dulat_variants = [v.strip() for v in row.dulat.split(";") if v.strip()]
        pos_variants = [v.strip() for v in row.pos.split(";") if v.strip()]
        gloss_variants = [v.strip() for v in row.gloss.split(";") if v.strip()]

        if not self._is_mixed_baal_pattern(
            analysis_variants=analysis_variants,
            dulat_variants=dulat_variants,
            pos_variants=pos_variants,
            gloss_variants=gloss_variants,
        ):
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="bˤl(II)/m",
            dulat="bʕl (II)",
            pos="n. m.",
            gloss="lord",
            comment=row.comment,
        )

    def _is_mixed_baal_pattern(
        self,
        analysis_variants: list[str],
        dulat_variants: list[str],
        pos_variants: list[str],
        gloss_variants: list[str],
    ) -> bool:
        has_ii_singular_style = any(v in {"bˤl(II)/", "bˤlm(II)/"} for v in analysis_variants)
        has_ii_plural_style = "bˤl(II)/m" in analysis_variants
        has_i_plural = "bˤl(I)/m" in analysis_variants
        if not ((has_ii_singular_style or has_ii_plural_style) and has_i_plural):
            return False

        has_dulat_pair = {"bʕl (II)", "bʕl (I)"}.issubset(set(dulat_variants))
        if not has_dulat_pair:
            return False

        has_labourer_gloss = any("labourer" in g for g in gloss_variants)
        return has_labourer_gloss
