"""Normalize III-aleph noun/adjective case-vowel encoding.

For final-aleph lexemes, enforce explicit reconstructed lexeme vowel and
surface-only case vowel encoding:
- lexical: `(u` / `(i` / `(a`
- inflectional: `/&u` / `/&i` / `/&a`
"""

from __future__ import annotations

import re
from typing import Optional

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate

_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_ANALYSIS_BASE_RE = re.compile(r"^(?P<lemma>[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+)(?P<hom>\([IVX]+\))?/$")
_ANALYSIS_SPLIT_M_RE = re.compile(r"^(?P<lemma>[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+)(?P<hom>\([IVX]+\))?/m$")
_A_LEPH_VOWELS = {"u", "i", "a"}


def _split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",")]


def _parse_declared_token(token: str) -> tuple[str, str]:
    tok = (token or "").strip()
    if not tok or tok == "?" or tok.startswith("/"):
        return "", ""
    match = _TOKEN_RE.match(tok)
    if not match:
        return tok, ""
    return (match.group(1) or "").strip(), (match.group(2) or "").strip()


class IIIAlephCaseFixer(RefinementStep):
    """Rewrite III-aleph noun/adjective variants to `(V/&X` encoding."""

    def __init__(self, gate: Optional[DulatMorphGate] = None) -> None:
        self._gate = gate

    @property
    def name(self) -> str:
        return "iii-aleph-case"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row

        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)

        changed = False
        out_analysis: list[str] = []
        for idx, analysis_variant in enumerate(analysis_variants):
            dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
            pos_variant = pos_variants[idx] if idx < len(pos_variants) else ""
            dulat_head = _split_comma(dulat_variant)[0] if dulat_variant else ""
            pos_head = _split_comma(pos_variant)[0] if pos_variant else ""
            rewritten = self._rewrite_variant(
                surface=row.surface,
                analysis_variant=analysis_variant,
                dulat_head=dulat_head,
                pos_head=pos_head,
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
        surface: str,
        analysis_variant: str,
        dulat_head: str,
        pos_head: str,
    ) -> str:
        value = (analysis_variant or "").strip()
        if not value or value == "?":
            return value
        if any(ch in value for ch in ("+", "~", "[")):
            return value
        if "/&" in value:
            return value
        if not (value.endswith("/") or value.endswith("/m")):
            return value

        pos_lower = (pos_head or "").lower()
        if not (pos_lower.startswith("n.") or pos_lower.startswith("adj.")):
            return value

        lemma, declared_homonym = _parse_declared_token(dulat_head)
        if not lemma:
            return value

        surface_norm = normalize_surface(surface).lower()
        lemma_norm = normalize_surface(lemma).lower()
        if len(surface_norm) < 2 or len(lemma_norm) < 2:
            return value

        lex_vowel = lemma_norm[-1]
        if lex_vowel not in _A_LEPH_VOWELS:
            return value

        plural_rewrite = self._rewrite_plural_m_variant(
            value=value,
            surface_norm=surface_norm,
            lemma_norm=lemma_norm,
            lex_vowel=lex_vowel,
            declared_homonym=declared_homonym,
            dulat_head=dulat_head,
            surface=surface,
        )
        if plural_rewrite is not None:
            return plural_rewrite

        surface_vowel = surface_norm[-1]
        if surface_vowel not in _A_LEPH_VOWELS:
            return value
        if surface_norm[:-1] != lemma_norm[:-1]:
            return value

        reconstructed = normalize_surface(reconstruct_surface_from_analysis(value)).lower()
        if reconstructed == surface_norm:
            return value

        match = _ANALYSIS_BASE_RE.match(value)
        if not match:
            return value
        analysis_lemma = (match.group("lemma") or "").strip()
        analysis_homonym = (match.group("hom") or "").strip()
        analysis_lemma_norm = normalize_surface(analysis_lemma).lower()
        if len(analysis_lemma_norm) < 2:
            return value
        if analysis_lemma_norm[-1] not in _A_LEPH_VOWELS:
            return value
        if analysis_lemma_norm[:-1] != surface_norm[:-1]:
            return value

        rendered_base = analysis_lemma[:-1]
        if not rendered_base:
            return value

        homonym = analysis_homonym
        if not homonym and declared_homonym:
            homonym = f"({declared_homonym})"

        return f"{rendered_base}({lex_vowel}{homonym}/&{surface_vowel}"

    def _rewrite_plural_m_variant(
        self,
        *,
        value: str,
        surface_norm: str,
        lemma_norm: str,
        lex_vowel: str,
        declared_homonym: str,
        dulat_head: str,
        surface: str,
    ) -> Optional[str]:
        """Rewrite III-aleph plural -m forms to `(V&X/m` encoding."""
        if "&" in value:
            return None
        if len(surface_norm) < 3 or not surface_norm.endswith("m"):
            return None
        surface_vowel = surface_norm[-2]
        if surface_vowel not in _A_LEPH_VOWELS:
            return None
        if surface_norm[:-2] != lemma_norm[:-1]:
            return None
        if not self._has_plural_surface_morphology(dulat_head=dulat_head, surface=surface):
            return None

        match = _ANALYSIS_SPLIT_M_RE.match(value)
        if match:
            analysis_lemma = (match.group("lemma") or "").strip()
            analysis_homonym = (match.group("hom") or "").strip()
        else:
            match = _ANALYSIS_BASE_RE.match(value)
            if not match:
                return None
            analysis_lemma = (match.group("lemma") or "").strip()
            analysis_homonym = (match.group("hom") or "").strip()

        analysis_lemma_norm = normalize_surface(analysis_lemma).lower()
        if len(analysis_lemma_norm) < 2:
            return None
        if analysis_lemma_norm[-1] not in _A_LEPH_VOWELS:
            return None
        if analysis_lemma_norm[:-1] != surface_norm[:-2]:
            return None

        rendered_base = analysis_lemma[:-1]
        if not rendered_base:
            return None

        homonym = analysis_homonym
        if not homonym and declared_homonym:
            homonym = f"({declared_homonym})"

        if surface_vowel == lex_vowel:
            return f"{rendered_base}({lex_vowel}{homonym}&/m"
        return f"{rendered_base}({lex_vowel}{homonym}&{surface_vowel}/m"

    def _has_plural_surface_morphology(self, *, dulat_head: str, surface: str) -> bool:
        if self._gate is None:
            return False
        morphologies = self._gate.surface_morphologies(dulat_head, surface)
        if not morphologies:
            return False
        return any("pl." in morph for morph in morphologies)
