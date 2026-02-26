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
_SPLIT_FEM_T_RE = re.compile(r"^(?P<stem>.+?)(?P<hom>\([IVX]+\))?/t(?P<plural_eq>=?)$")
_BASE_NOMINAL_RE = re.compile(r"^(?P<stem>[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+)(?P<hom>\([IVX]+\))?/$")
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_LEMMA_LETTER_RE = re.compile(r"[^A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_PL_TANT_RE = re.compile(
    r"(?:\bpl\.?\s*tant\b|\bplur(?:ale)?\.?\s*tant(?:um|u)?\b)\.?\??",
    flags=re.IGNORECASE,
)
_SINGULAR_FORM_RE = re.compile(r"\bsg\.", flags=re.IGNORECASE)
_SINGULAR_FORM_WORD_RE = re.compile(r"\bsing", flags=re.IGNORECASE)
_PLURAL_FORM_RE = re.compile(r"\bpl\.", flags=re.IGNORECASE)
_PLURAL_FORM_WORD_RE = re.compile(r"\bplur", flags=re.IGNORECASE)
_FORCED_FEMININE_PLURAL_T_EQUAL_KEYS: set[tuple[str, str]] = {
    ("hmlt", ""),
    ("ṯnt", "II"),
}


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


def _has_feminine_morph_marker(morphologies: set[str]) -> bool:
    for morph in morphologies:
        parts = _split_comma((morph or "").lower())
        if any(part == "f." for part in parts):
            return True
    return False


class FeminineTSingularSplitFixer(RefinementStep):
    """Normalize feminine /t split for noun-like analyses (/t and /t=)."""

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
        if value.endswith(("/m", "/m=")):
            return value

        lemma_has_final_t = _declared_lemma_has_final_t(dulat_slot)
        surface_has_terminal_t = normalize_surface(surface).endswith("t")

        if not self._is_feminine_context(
            pos_slot=pos_slot,
            dulat_slot=dulat_slot,
            surface=surface,
        ):
            if not (
                lemma_has_final_t
                and surface_has_terminal_t
                and (
                    _is_generic_nominal_without_gender(pos_slot)
                    or _is_generic_numeral_without_gender(pos_slot)
                )
            ):
                return value

        declared_homonym = _declared_homonym(dulat_slot)
        is_pos_pl_tant = _has_plurale_tantum_marker(pos_slot) or _is_forced_plural_t_token(
            dulat_slot
        )
        has_sg_pl_ambiguous_surface = (
            not is_pos_pl_tant
            and not _is_numeral_pos(pos_slot)
            and self._surface_has_singular_and_plural_morphology(
                dulat_slot=dulat_slot,
                surface=surface,
            )
        )

        base_match = _BASE_NOMINAL_RE.match(value)
        if (
            base_match
            and value.endswith("/")
            and normalize_surface(surface).endswith("t")
            and not normalize_surface(base_match.group("stem")).lower().endswith("t")
        ):
            stem = base_match.group("stem")
            homonym = base_match.group("hom") or declared_homonym
            rewritten = _render_feminine_t_split(
                stem=stem,
                homonym=homonym,
                lexical_t=lemma_has_final_t,
                plural=is_pos_pl_tant,
            )
            return _with_surface_terminal_m(rewritten, surface=surface)

        unsplit_match = _UNSPLIT_FEM_T_RE.match(value)
        if unsplit_match:
            if has_sg_pl_ambiguous_surface:
                stem = unsplit_match.group("stem")
                homonym = unsplit_match.group("hom") or declared_homonym
                singular = _render_feminine_t_split(
                    stem=stem,
                    homonym=homonym,
                    lexical_t=lemma_has_final_t,
                    plural=False,
                )
                plural = _render_feminine_t_split(
                    stem=stem,
                    homonym=homonym,
                    lexical_t=lemma_has_final_t,
                    plural=True,
                )
                return _join_unique_variants(
                    [
                        _with_surface_terminal_m(singular, surface=surface),
                        _with_surface_terminal_m(plural, surface=surface),
                    ]
                )
            if (
                self._is_plural_dulat_token(dulat_slot, surface=surface)
                and not is_pos_pl_tant
                and not _is_numeral_pos(pos_slot)
            ):
                return value
            stem = unsplit_match.group("stem")
            homonym = unsplit_match.group("hom") or declared_homonym
            rewritten = _render_feminine_t_split(
                stem=stem,
                homonym=homonym,
                lexical_t=lemma_has_final_t,
                plural=is_pos_pl_tant,
            )
            return _with_surface_terminal_m(rewritten, surface=surface)

        split_match = _SPLIT_FEM_T_RE.match(value)
        if not split_match:
            return value
        if not lemma_has_final_t:
            return value

        stem = split_match.group("stem")
        homonym = split_match.group("hom") or declared_homonym
        split_is_t_equal = bool(split_match.group("plural_eq"))
        rewritten = _render_feminine_t_split(
            stem=stem,
            homonym=homonym,
            lexical_t=True,
            plural=split_is_t_equal or is_pos_pl_tant,
        )
        return _with_surface_terminal_m(rewritten, surface=surface)

    def _is_plural_dulat_token(self, token: str, surface: str = "") -> bool:
        if self._gate is None:
            return False
        token = (token or "").strip()
        if not token or token == "?":
            return False
        return self._gate.is_plural_token(token, surface=surface)

    def _is_feminine_context(self, pos_slot: str, dulat_slot: str, surface: str) -> bool:
        pos_text = (pos_slot or "").strip()
        if not pos_text:
            return self._surface_has_feminine_morphology(dulat_slot=dulat_slot, surface=surface)

        upper = pos_text.upper()
        if "N. F." in upper or "ADJ. F." in upper:
            return True

        if any(tag in upper for tag in _ONOMASTIC_POS_TAGS):
            if " F." in upper or upper.startswith("F."):
                return True
            return self._is_feminine_onomastic_token(dulat_slot)

        # DULAT form morphology can mark feminine forms for masculine lemmas
        # (e.g., pḥl -> pḥlt). Allow split in that case.
        if (
            upper.startswith("N.") or upper.startswith("ADJ.")
        ) and self._surface_has_feminine_morphology(dulat_slot=dulat_slot, surface=surface):
            return True

        return False

    def _is_feminine_onomastic_token(self, token: str) -> bool:
        normalized = OnomasticOverrideStore.normalize_key(token)
        if not normalized:
            return False
        return normalized in self._feminine_onomastic_tokens

    def _surface_has_feminine_morphology(self, dulat_slot: str, surface: str) -> bool:
        morphologies = self._surface_morphologies(dulat_slot=dulat_slot, surface=surface)
        if not morphologies:
            return False
        return _has_feminine_morph_marker(morphologies)

    def _surface_has_singular_and_plural_morphology(self, dulat_slot: str, surface: str) -> bool:
        morphologies = self._surface_morphologies(dulat_slot=dulat_slot, surface=surface)
        if not morphologies:
            return False
        has_singular = any(_has_singular_form_marker(morph) for morph in morphologies)
        has_plural = any(_has_plural_form_marker(morph) for morph in morphologies)
        return has_singular and has_plural

    def _surface_morphologies(self, dulat_slot: str, surface: str) -> set[str]:
        if self._gate is None:
            return set()
        token = (dulat_slot or "").strip()
        if not token or token == "?":
            return set()
        return self._gate.surface_morphologies(token, surface=surface)


def _has_singular_form_marker(morph: str) -> bool:
    text = (morph or "").lower()
    if not text:
        return False
    return bool(_SINGULAR_FORM_RE.search(text) or _SINGULAR_FORM_WORD_RE.search(text))


def _has_plural_form_marker(morph: str) -> bool:
    text = (morph or "").lower()
    if not text:
        return False
    return bool(_PLURAL_FORM_RE.search(text) or _PLURAL_FORM_WORD_RE.search(text))


def _join_unique_variants(variants: Sequence[str]) -> str:
    unique: list[str] = []
    for variant in variants:
        value = (variant or "").strip()
        if not value:
            continue
        if value in unique:
            continue
        unique.append(value)
    if not unique:
        return ""
    return ";".join(unique)


def _has_plurale_tantum_marker(value: str) -> bool:
    return _PL_TANT_RE.search(value or "") is not None


def _is_generic_nominal_without_gender(pos_slot: str) -> bool:
    """Return True for noun/adjective POS tags without explicit gender."""
    upper = (pos_slot or "").strip().upper()
    if not (upper.startswith("N.") or upper.startswith("ADJ.")):
        return False
    if " M." in upper or upper.startswith("M."):
        return False
    if " F." in upper or upper.startswith("F."):
        return False
    return True


def _is_generic_numeral_without_gender(pos_slot: str) -> bool:
    """Return True for numeral POS tags without explicit gender."""
    upper = (pos_slot or "").strip().upper()
    if not _is_numeral_pos(upper):
        return False
    if " M." in upper or upper.startswith("M."):
        return False
    if " F." in upper or upper.startswith("F."):
        return False
    return True


def _is_numeral_pos(pos_slot: str) -> bool:
    return (pos_slot or "").strip().upper().startswith("NUM.")


def _is_forced_plural_t_token(dulat_slot: str) -> bool:
    token = (dulat_slot or "").strip()
    if not token or token == "?" or token.startswith("/"):
        return False
    if "," in token:
        token = token.split(",", 1)[0].strip()
    match = _TOKEN_RE.match(token)
    lemma = (match.group(1) if match else token).strip()
    hom = (match.group(2) if match else "") or ""
    key = (normalize_surface(lemma), hom)
    return key in _FORCED_FEMININE_PLURAL_T_EQUAL_KEYS


def _render_feminine_t_split(
    stem: str,
    homonym: str,
    lexical_t: bool,
    plural: bool = False,
) -> str:
    ending = "/t=" if plural else "/t"
    if lexical_t:
        if stem.endswith("(t"):
            return f"{stem}{homonym}{ending}"
        return f"{stem}(t{homonym}{ending}"
    return f"{stem}{homonym}{ending}"


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
