"""Normalize /b-ʕ-l/ verbal variants to canonical `...[/` analysis form."""

from pipeline.steps.base import RefinementStep, TabletRow

_BAAL_VERBAL_DULAT = "/b-ʕ-l/"


def _split_variants(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _normalize_baal_variant(analysis_variant: str, dulat_variant: str) -> str:
    if (dulat_variant or "").strip() != _BAAL_VERBAL_DULAT:
        return analysis_variant
    variant = (analysis_variant or "").strip()
    if variant.endswith("[") and "/" not in variant:
        return f"{variant}/"
    return analysis_variant


class BaalVerbalSlashFixer(RefinementStep):
    """Ensure verbal /b-ʕ-l/ analyses keep reconstructable `[/` closure."""

    @property
    def name(self) -> str:
        return "baal-verbal-slash"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_variants(row.analysis)
        dulat_variants = _split_variants(row.dulat)

        if (
            not analysis_variants
            or not dulat_variants
            or len(analysis_variants) != len(dulat_variants)
        ):
            normalized_analysis = _normalize_baal_variant(row.analysis, row.dulat)
            if normalized_analysis == row.analysis:
                return row
            return TabletRow(
                line_id=row.line_id,
                surface=row.surface,
                analysis=normalized_analysis,
                dulat=row.dulat,
                pos=row.pos,
                gloss=row.gloss,
                comment=row.comment,
            )

        normalized_variants: list[str] = []
        changed = False
        for analysis_variant, dulat_variant in zip(analysis_variants, dulat_variants):
            normalized = _normalize_baal_variant(analysis_variant, dulat_variant)
            if normalized != analysis_variant:
                changed = True
            normalized_variants.append(normalized)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(normalized_variants),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )
