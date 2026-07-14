"""Split noun/adjective terminal y/h as case ending when morphology supports it."""

from __future__ import annotations

import re
from typing import Optional

from pipeline.steps.analysis_utils import normalize_surface
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate

_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_BASE_NOMINAL_RE = re.compile(r"^(?P<lemma>[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+)(?P<hom>\([IVX]+\))?/$")
_CASE_SUFFIXES = {"y", "h"}


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


def _parse_declared_dulat_token(token: str) -> tuple[str, str]:
    tok = (token or "").strip()
    if not tok or tok == "?" or tok.startswith("/"):
        return "", ""
    m = _TOKEN_RE.match(tok)
    if not m:
        return tok, ""
    return (m.group(1) or "").strip(), (m.group(2) or "").strip()


def _is_nominal_or_adjectival(pos_slot: str) -> bool:
    lower = (pos_slot or "").strip().lower()
    return lower.startswith("n.") or lower.startswith("adj.")


def _morphology_is_suffix_only(morphologies: set[str]) -> bool:
    if not morphologies:
        return False
    return all("suff" in morph for morph in morphologies)


class NominalCaseEndingYHFixer(RefinementStep):
    """Rewrite `...y/` or `...h/` style analyses to explicit `/y` or `/h`."""

    def __init__(self, gate: Optional[DulatMorphGate] = None) -> None:
        self._gate = gate

    @property
    def name(self) -> str:
        return "nominal-case-ending-yh"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row

        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)
        changed = False
        out_variants: list[str] = []

        for idx, variant in enumerate(analysis_variants):
            dulat_slot = dulat_variants[idx] if idx < len(dulat_variants) else ""
            pos_slot = pos_variants[idx] if idx < len(pos_variants) else ""
            dulat_head = _split_comma(dulat_slot)[0] if dulat_slot else ""
            pos_head = _split_comma(pos_slot)[0] if pos_slot else ""
            rewritten = self._rewrite_variant(
                surface=row.surface,
                analysis_variant=variant,
                dulat_head=dulat_head,
                pos_head=pos_head,
            )
            if rewritten != variant:
                changed = True
            out_variants.append(rewritten)

        if not changed:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(out_variants),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _rewrite_variant(
        self,
        surface: str,
        analysis_variant: str,
        dulat_head: str,
        pos_head: str,
    ) -> str:
        value = (analysis_variant or "").strip()
        if not value or value == "?":
            return value
        if not _is_nominal_or_adjectival(pos_head):
            return value
        if any(ch in value for ch in ("+", "~", "[")):
            return value

        match = _BASE_NOMINAL_RE.match(value)
        if not match:
            return value

        surface_norm = normalize_surface(surface).lower()
        if len(surface_norm) < 2:
            return value
        suffix = surface_norm[-1]
        if suffix not in _CASE_SUFFIXES:
            return value

        declared_lemma, declared_hom = _parse_declared_dulat_token(dulat_head)
        declared_norm = normalize_surface(declared_lemma).lower()
        if not declared_norm or len(declared_norm) < 2:
            return value

        if self._gate is None:
            return value
        morphologies = self._gate.surface_morphologies(dulat_head, surface=surface)
        # Do not use case-ending split for pure suffixal forms.
        if _morphology_is_suffix_only(morphologies):
            return value

        analysis_lemma = (match.group("lemma") or "").strip()
        analysis_hom = (match.group("hom") or "").strip()
        analysis_norm = normalize_surface(analysis_lemma).lower()
        stem_norm = surface_norm[:-1]

        # Two safe normalization cases:
        # 1) analysis already includes trailing y/h in lemma (umy/ -> um/y)
        # 2) analysis omits trailing y/h while surface has it (hkl/ -> hkl/y)
        if analysis_norm == surface_norm and declared_norm == stem_norm:
            stem = analysis_lemma[:-1]
        elif analysis_norm == stem_norm and declared_norm == stem_norm:
            stem = analysis_lemma
        else:
            return value

        if not stem:
            return value

        homonym = analysis_hom
        if not homonym and declared_hom:
            homonym = f"({declared_hom})"

        return f"{stem}{homonym}/{suffix}"
