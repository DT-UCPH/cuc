"""Rewrite DULAT note-backed enclitic `-m` forms to `~m` encoding."""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.config.dulat_form_note_index import DulatFormNoteIndex
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.verb_form_encoding_split import (
    _requires_finite_encoding,
    _requires_infinitive_encoding,
    _requires_participle_encoding,
    _split_semicolon,
    _split_slash_options,
    _to_finite_encoding,
    _to_infinitive_encoding,
    _to_participle_encoding,
)

_HOMONYM_RE = re.compile(r"\(([IVX]+)\)(?=(?:\[|/))")


class DulatEncliticMFixer(RefinementStep):
    """Apply `~m` when an exact DULAT form note marks enclitic `-m`."""

    def __init__(self, dulat_db: Path, note_index: DulatFormNoteIndex | None = None) -> None:
        self._note_index = note_index or DulatFormNoteIndex.from_sqlite(dulat_db)

    @property
    def name(self) -> str:
        return "dulat-enclitic-m"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if not row.surface or not row.surface.endswith("m"):
            return row
        analysis_variants = _split_semicolon(row.analysis)
        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)
        if not analysis_variants or not dulat_variants:
            return row

        changed = False
        out_analysis: list[str] = []
        for idx, analysis in enumerate(analysis_variants):
            dulat = (
                dulat_variants[idx]
                if idx < len(dulat_variants)
                else (dulat_variants[0] if dulat_variants else "")
            )
            pos = (
                pos_variants[idx]
                if idx < len(pos_variants)
                else (pos_variants[0] if pos_variants else "")
            )
            rewritten = self._rewrite_variant(
                surface=row.surface, analysis=analysis, dulat=dulat, pos=pos
            )
            if rewritten != analysis:
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

    def _rewrite_variant(self, *, surface: str, analysis: str, dulat: str, pos: str) -> str:
        if "~m" in (analysis or ""):
            return analysis
        if not self._note_index.has_enclitic_m(surface=surface, dulat_token=dulat):
            return analysis

        host_surface = surface[:-1]
        if not host_surface:
            return analysis

        host_analysis = _replace_analysis_host(host_surface, analysis)
        options = _split_slash_options(pos)
        if any(_requires_infinitive_encoding(option) for option in options):
            base = _to_infinitive_encoding(host_surface, host_analysis, dulat)
        elif any(_requires_participle_encoding(option) for option in options):
            base = _to_participle_encoding(host_surface, host_analysis, dulat)
        elif any(_requires_finite_encoding(option) for option in options):
            base = _to_finite_encoding(host_analysis)
        else:
            base = host_analysis

        if not base or "~m" in base:
            return analysis
        return f"{base}~m"


def _replace_analysis_host(surface: str, analysis: str) -> str:
    text = (analysis or "").strip()
    if not text:
        return surface
    cut_points = [idx for idx in (text.find("["), text.find("/")) if idx != -1]
    if not cut_points:
        return surface
    cut_idx = min(cut_points)
    suffix = text[cut_idx:]
    homonym_match = _HOMONYM_RE.search(text)
    homonym = homonym_match.group(0) if homonym_match else ""
    return f"{surface}{homonym}{suffix}"
