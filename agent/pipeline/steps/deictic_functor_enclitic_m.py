"""Encode deictic functor extended -m forms as '~m' enclitic variants."""

from __future__ import annotations

from typing import Optional

from pipeline.steps.analysis_utils import normalize_surface
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


class DeicticFunctorEncliticMFixer(RefinementStep):
    """Convert deictic functor base forms to attested extended ~m forms."""

    def __init__(self, gate: Optional[DulatMorphGate] = None) -> None:
        self._gate = gate

    @property
    def name(self) -> str:
        return "deictic-functor-enclitic-m"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if self._gate is None:
            return row

        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row

        pos_variants = _split_semicolon(row.pos)
        dulat_variants = _split_semicolon(row.dulat)
        changed = False
        out_analysis: list[str] = []

        for idx, analysis_variant in enumerate(analysis_variants):
            pos_variant = pos_variants[idx] if idx < len(pos_variants) else ""
            dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
            pos_head = _split_comma(pos_variant)[0] if pos_variant else ""
            dulat_head = _split_comma(dulat_variant)[0] if dulat_variant else ""
            rewritten = self._rewrite_variant(
                analysis_variant=analysis_variant,
                pos_head=pos_head,
                dulat_head=dulat_head,
                surface=row.surface,
            )
            if rewritten != analysis_variant:
                changed = True
            out_analysis.append(rewritten)

        if not changed:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(out_analysis),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _rewrite_variant(
        self,
        analysis_variant: str,
        pos_head: str,
        dulat_head: str,
        surface: str,
    ) -> str:
        value = (analysis_variant or "").strip()
        if not value or value == "?":
            return value
        if any(ch in value for ch in ("+", "~", "/", "[")):
            return value

        pos_lower = (pos_head or "").strip().lower()
        if "deictic" not in pos_lower or "functor" not in pos_lower:
            return value

        surface_norm = normalize_surface(surface).lower()
        value_norm = normalize_surface(value).lower()
        if not surface_norm.endswith("m"):
            return value
        if value_norm != surface_norm[:-1]:
            return value
        if not self._gate.has_surface_form(dulat_head, surface=surface):
            return value

        return f"{value}~m"
