"""Normalize raw verbal suffix-pronoun tails into `+suffix` payload notation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.verb_form_morph_pos import VerbFormMorphIndex

_FORM_SUFFC_RE = re.compile(r"\bsuffc\.", flags=re.IGNORECASE)
_FORM_PREFC_RE = re.compile(r"\bprefc\.", flags=re.IGNORECASE)
_FORM_IMPV_RE = re.compile(r"\bimpv\.", flags=re.IGNORECASE)
_FORM_INF_RE = re.compile(r"\binf\.", flags=re.IGNORECASE)
_FORM_PTC_RE = re.compile(r"\bptcpl\.", flags=re.IGNORECASE)
_EXPLICIT_SUFFC_MORPH_RE = re.compile(r"\b(?:suffc|csuff)\b", flags=re.IGNORECASE)
_BARE_SUFF_RE = re.compile(r"\bsuff\.", flags=re.IGNORECASE)
_WITH_SUFF_RE = re.compile(r"\bwith\s+suff\.", flags=re.IGNORECASE)
_STEM_MARKERS = (":pass", ":d", ":l", ":r")
_SUFFIX_SEGMENTS = ("nkm", "hm", "hn", "km", "kn", "ny", "nh", "nk", "nm", "nn", "h", "k", "n", "y")


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _is_target_pos(pos_text: str) -> bool:
    text = (pos_text or "").strip().lower()
    if "vb" not in text:
        return False
    if _FORM_SUFFC_RE.search(text):
        return False
    return bool(
        _FORM_PREFC_RE.search(text)
        or _FORM_IMPV_RE.search(text)
        or _FORM_INF_RE.search(text)
        or _FORM_PTC_RE.search(text)
    )


def _supports_pronominal_suffix_note(morphologies: set[str]) -> bool:
    for morphology in morphologies:
        text = (morphology or "").strip().lower()
        if not text:
            continue
        if _EXPLICIT_SUFFC_MORPH_RE.search(text):
            continue
        if not (_BARE_SUFF_RE.search(text) or _WITH_SUFF_RE.search(text)):
            continue
        if (
            _FORM_PREFC_RE.search(text)
            or _FORM_IMPV_RE.search(text)
            or _FORM_INF_RE.search(text)
            or _FORM_PTC_RE.search(text)
        ):
            return True
    return False


def _split_tail_suffix(tail: str) -> tuple[str, str] | None:
    for suffix in _SUFFIX_SEGMENTS:
        if tail == suffix:
            return suffix, ""
        for marker in _STEM_MARKERS:
            if tail == f"{suffix}{marker}":
                return suffix, marker
    return None


class VerbPronominalSuffixTailFixer(RefinementStep):
    """Rewrite raw `[k`, `[h:l`, etc. to canonical verbal `+suffix` payloads."""

    def __init__(
        self,
        dulat_db: Path,
        form_index: Optional[VerbFormMorphIndex] = None,
    ) -> None:
        self._index = form_index or VerbFormMorphIndex.from_sqlite(dulat_db)

    @property
    def name(self) -> str:
        return "verb-pronominal-suffix-tail"

    def refine_row(self, row: TabletRow) -> TabletRow:
        morphologies = self._index.morphologies_for(row.surface or "", row.dulat or "")
        if not _supports_pronominal_suffix_note(morphologies):
            return row

        analysis_variants = _split_semicolon(row.analysis)
        pos_variants = _split_semicolon(row.pos)
        if not analysis_variants or not pos_variants:
            return row

        changed = False
        out_analysis: list[str] = []
        for idx, analysis_variant in enumerate(analysis_variants):
            pos_variant = pos_variants[idx] if idx < len(pos_variants) else ""
            rewritten = self._rewrite_variant(
                surface=row.surface,
                analysis_variant=analysis_variant,
                pos_variant=pos_variant,
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

    def _rewrite_variant(self, *, surface: str, analysis_variant: str, pos_variant: str) -> str:
        value = (analysis_variant or "").strip()
        if not _is_target_pos(pos_variant):
            return value
        if not value or "[/" in value or "+" in value or "~" in value or "[" not in value:
            return value

        head, tail = value.split("[", 1)
        parsed = _split_tail_suffix(tail)
        if parsed is None:
            return value
        suffix, marker = parsed
        candidate_tail = f"{marker}+{suffix}" if marker else f"+{suffix}"
        candidate = f"{head}[{candidate_tail}"
        if normalize_surface(reconstruct_surface_from_analysis(candidate)) != normalize_surface(
            surface
        ):
            return value
        return candidate
