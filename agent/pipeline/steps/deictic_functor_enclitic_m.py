"""Encode deictic functor extended -m forms as '~m' enclitic variants."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipeline.config.dulat_form_note_index import DulatFormNoteIndex
from pipeline.steps.analysis_utils import normalize_surface
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


class DeicticFunctorEncliticMFixer(RefinementStep):
    """Convert deictic functor base forms to attested extended ~m forms."""

    def __init__(
        self,
        gate: Optional[DulatMorphGate] = None,
        dulat_db: Optional[Path] = None,
        note_index: Optional[DulatFormNoteIndex] = None,
    ) -> None:
        self._gate = gate
        self._note_index = note_index or (
            DulatFormNoteIndex.from_sqlite(dulat_db) if dulat_db is not None else None
        )

    @property
    def name(self) -> str:
        return "deictic-functor-enclitic-m"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if self._gate is None and self._note_index is None:
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
        if self._gate is not None and self._gate.has_surface_form(dulat_head, surface=surface):
            return f"{value}~m"
        if self._note_index is None:
            return value
        if not self._note_index.has_extended_m_surface(surface=surface, dulat_token=dulat_head):
            return value

        return f"{value}~m"
