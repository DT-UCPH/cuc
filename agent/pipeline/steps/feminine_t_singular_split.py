"""Fix unsplit feminine singular noun endings: Xt/ -> X/t or X(t(hom)/t."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Sequence

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate
from pipeline.steps.onomastic_overrides import OnomasticOverrideStore

_ONOMASTIC_POS_TAGS: Sequence[str] = ("DN", "PN", "TN", "GN", "MN")
_UNSPLIT_FEM_T_RE = re.compile(r"^(?P<stem>.+?)t(?P<hom>\([IVX]+\))?/$")
_SPLIT_FEM_T_RE = re.compile(r"^(?P<stem>.+?)(?P<hom>\([IVX]+\))?/t$")
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_LEMMA_LETTER_RE = re.compile(r"[^A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


class FeminineTSingularSplitFixer(RefinementStep):
    """Apply feminine singular /t split to noun-like analyses."""

    def __init__(
        self,
        overrides_path: Path | None = None,
        feminine_onomastic_tokens: set[str] | None = None,
        gate: Optional[DulatMorphGate] = None,
    ) -> None:
        self._overrides_path = overrides_path or Path("data/onomastic_gloss_overrides.tsv")
        self._gate = gate
        if feminine_onomastic_tokens is None:
            store = OnomasticOverrideStore.from_tsv(self._overrides_path)
            self._feminine_onomastic_tokens = store.feminine_tokens()
        else:
            self._feminine_onomastic_tokens = {
                OnomasticOverrideStore.normalize_key(token)
                for token in feminine_onomastic_tokens
                if (token or "").strip()
            }

    @property
    def name(self) -> str:
        return "feminine-t-singular-split"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row

        pos_variants = _split_semicolon(row.pos)
        dulat_variants = _split_semicolon(row.dulat)

        changed = False
        out_variants: list[str] = []
        for idx, analysis_variant in enumerate(analysis_variants):
            pos_variant = pos_variants[idx] if idx < len(pos_variants) else ""
            dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
            pos_head = _split_comma(pos_variant)[0].strip() if pos_variant else ""
            dulat_head = _split_comma(dulat_variant)[0].strip() if dulat_variant else ""
            transformed = self._fix_variant(
                variant=analysis_variant,
                pos_slot=pos_head,
                dulat_slot=dulat_head,
                surface=row.surface,
            )
            out_variants.append(transformed)
            if transformed != analysis_variant:
                changed = True

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

    def _fix_variant(self, variant: str, pos_slot: str, dulat_slot: str, surface: str) -> str:
        value = (variant or "").strip()
        if not value or value == "?":
            return value
        if "+" in value or "~" in value:
            return value
        if "[" in value:
            return value
        if value.endswith(("/m", "/m=", "/t=")):
            return value

        if not self._is_feminine_context(pos_slot=pos_slot, dulat_slot=dulat_slot):
            return value

        lemma_has_final_t = _declared_lemma_has_final_t(dulat_slot)
        declared_homonym = _declared_homonym(dulat_slot)

        unsplit_match = _UNSPLIT_FEM_T_RE.match(value)
        if unsplit_match:
            if self._is_plural_dulat_token(dulat_slot, surface=surface):
                return value
            stem = unsplit_match.group("stem")
            homonym = unsplit_match.group("hom") or declared_homonym
            rewritten = _render_feminine_t_split(
                stem=stem,
                homonym=homonym,
                lexical_t=lemma_has_final_t,
            )
            return _with_surface_terminal_m(rewritten, surface=surface)

        split_match = _SPLIT_FEM_T_RE.match(value)
        if not split_match:
            return value
        if not lemma_has_final_t:
            return value

        stem = split_match.group("stem")
        homonym = split_match.group("hom") or declared_homonym
        rewritten = _render_feminine_t_split(
            stem=stem,
            homonym=homonym,
            lexical_t=True,
        )
        return _with_surface_terminal_m(rewritten, surface=surface)

    def _is_plural_dulat_token(self, token: str, surface: str = "") -> bool:
        if self._gate is None:
            return False
        token = (token or "").strip()
        if not token or token == "?":
            return False
        return self._gate.is_plural_token(token, surface=surface)

    def _is_feminine_context(self, pos_slot: str, dulat_slot: str) -> bool:
        pos_text = (pos_slot or "").strip()
        if not pos_text:
            return False

        upper = pos_text.upper()
        if "PL. TANT" in upper:
            return False
        if "N. F." in upper or "ADJ. F." in upper:
            return True

        if any(tag in upper for tag in _ONOMASTIC_POS_TAGS):
            if " F." in upper or upper.startswith("F."):
                return True
            return self._is_feminine_onomastic_token(dulat_slot)

        return False

    def _is_feminine_onomastic_token(self, token: str) -> bool:
        normalized = OnomasticOverrideStore.normalize_key(token)
        if not normalized:
            return False
        return normalized in self._feminine_onomastic_tokens


def _render_feminine_t_split(stem: str, homonym: str, lexical_t: bool) -> str:
    if lexical_t:
        if stem.endswith("(t"):
            return f"{stem}{homonym}/t"
        return f"{stem}(t{homonym}/t"
    return f"{stem}{homonym}/t"


def _declared_lemma_has_final_t(dulat_slot: str) -> bool:
    token = (dulat_slot or "").strip()
    if not token or token == "?":
        return False
    if "," in token:
        token = token.split(",", 1)[0].strip()
    if token.startswith("/"):
        return False

    match = _TOKEN_RE.match(token)
    lemma = (match.group(1) if match else token).strip()
    if not lemma:
        return False
    normalized = normalize_surface(lemma)
    normalized_no_tail_group = re.sub(r"\([^)]*\)\s*$", "", normalized).strip()

    raw_letters = _LEMMA_LETTER_RE.sub("", normalized).lower()
    trimmed_letters = _LEMMA_LETTER_RE.sub("", normalized_no_tail_group).lower()
    return raw_letters.endswith("t") or trimmed_letters.endswith("t")


def _declared_homonym(dulat_slot: str) -> str:
    token = (dulat_slot or "").strip()
    if not token:
        return ""
    if "," in token:
        token = token.split(",", 1)[0].strip()
    match = _TOKEN_RE.match(token)
    if not match:
        return ""
    homonym = (match.group(2) or "").strip()
    if not homonym:
        return ""
    return f"({homonym})"


def _with_surface_terminal_m(analysis: str, surface: str) -> str:
    """Append inflectional terminal m when analysis is one letter short."""
    value = (analysis or "").strip()
    if not value:
        return value
    if not value.endswith("/t"):
        return value
    surface_norm = normalize_surface(surface).lower()
    if not surface_norm.endswith("m"):
        return value
    reconstructed = normalize_surface(reconstruct_surface_from_analysis(value)).lower()
    if reconstructed == surface_norm[:-1]:
        return f"{value}m"
    return value
