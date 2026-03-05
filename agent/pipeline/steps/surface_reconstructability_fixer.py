"""Repair recurring analysis/surface reconstructability mismatches."""

from __future__ import annotations

import re

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow

_ANALYSIS_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_RESTORABLE_TAIL_RE = re.compile(r"[mnhtywk]")
_PLAIN_LEMMA_ANALYSIS_RE = re.compile(r"^[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+(?:\([IVX]+\))?$")


def _split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",")]


def _analysis_letters(text: str) -> str:
    return "".join(ch for ch in (text or "") if _ANALYSIS_LETTER_RE.match(ch))


def _remove_spurious_tail_when_head_matches_surface(
    surface: str,
    analysis_variant: str,
) -> str:
    value = (analysis_variant or "").strip()
    if not value or "[" not in value:
        return analysis_variant
    if value.startswith("!"):
        return analysis_variant

    head, tail = value.split("[", 1)
    tail_text = (tail or "").strip()
    if not tail_text:
        return analysis_variant
    if any(ch in tail_text for ch in "+~:&="):
        return analysis_variant

    tail_letters = _analysis_letters(tail_text)
    if not tail_letters:
        return analysis_variant
    # Only trim pure-letter tails (for this recurrent `]š]qrb[b` class).
    if tail_letters != tail_text:
        return analysis_variant

    surface_letters = _analysis_letters(normalize_surface(surface))
    head_letters = _analysis_letters(head)
    if head_letters and head_letters == surface_letters:
        return f"{head}["
    return analysis_variant


class SurfaceReconstructabilityFixer(RefinementStep):
    """Normalize known recurrent form/analysis mismatch classes."""

    @property
    def name(self) -> str:
        return "surface-reconstructability"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if self._is_thmt_singular_row(row):
            return self._rewrite_thmt_singular(row)

        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row
        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)

        changed = False
        out_analysis: list[str] = []
        for idx, analysis_variant in enumerate(analysis_variants):
            dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
            dulat_head = _split_comma(dulat_variant)[0] if dulat_variant else ""
            pos_variant = pos_variants[idx] if idx < len(pos_variants) else ""
            rewritten = self._rewrite_variant(
                surface=row.surface,
                analysis_variant=analysis_variant,
                dulat_head=dulat_head,
                pos_variant=pos_variant,
            )
            if rewritten != analysis_variant:
                changed = True
            out_analysis.append(rewritten)

        out_pos = row.pos
        if (
            normalize_surface(row.surface).lower() == "thmtm"
            and row.dulat.strip() == "thmt"
            and "du." in (row.pos or "").lower()
        ):
            out_pos = "n. f."
            changed = True

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(out_analysis),
            dulat=row.dulat,
            pos=out_pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _is_thmt_singular_row(self, row: TabletRow) -> bool:
        return (
            normalize_surface(row.surface).lower() == "thmt"
            and row.dulat.strip() == "thmt"
            and row.pos.strip().startswith("n. f.")
        )

    def _rewrite_thmt_singular(self, row: TabletRow) -> TabletRow:
        analysis = "thm(t/t; thm/t"
        dulat = "thmt; thm"
        pos = "n. f.; n. m."
        gloss_primary = row.gloss.strip() or "Primordial Ocean"
        gloss = f"{gloss_primary}; ocean/deep"
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=analysis,
            dulat=dulat,
            pos=pos,
            gloss=gloss,
            comment=row.comment,
        )

    def _rewrite_variant(
        self,
        surface: str,
        analysis_variant: str,
        dulat_head: str,
        pos_variant: str,
    ) -> str:
        analysis_variant = _remove_spurious_tail_when_head_matches_surface(
            surface=surface,
            analysis_variant=analysis_variant,
        )
        surface_norm = normalize_surface(surface).lower()
        dulat = (dulat_head or "").strip()

        if dulat == "thmt" and surface_norm == "thmtm":
            return "thm(t/tm"

        if dulat == "ỉlt (I)":
            if surface_norm == "ilh":
                return "il(t(I)/&h"
            if surface_norm == "ilht":
                return "il(t(I)/&ht"

        if dulat == "ảṯt" and surface_norm == "aṯt":
            return _demote_t_equal_to_t(analysis_variant)

        if dulat == "ṯảt" and surface_norm == "ṯat":
            return _demote_t_equal_to_t(analysis_variant)

        if dulat == "bnt (II)":
            if surface_norm == "bnwt":
                return "bn&w(t(II)/t="
            if surface_norm == "bnwth":
                return "bn&w(t(II)/t=+h"

        if surface_norm == "mtm":
            if dulat == "mt (II)":
                return "mt(II)/~m"
            if dulat == "mt (I)":
                return "mt(I)/m"
            if dulat == "mt (III)":
                return "mt(III)/m"
            if dulat == "/m-t/":
                return "mt[~m"

        if dulat == "ym (I)":
            if surface_norm == "ymm":
                return "ym(I)/m"
            if surface_norm == "ymt":
                return "ym(I)/t="
            if surface_norm == "ymy":
                return "ym(I)&y/"

        restored = _restore_hidden_weak_y_before_enclitic_m(
            surface=surface,
            analysis_variant=analysis_variant,
            pos_variant=pos_variant,
        )
        if restored != analysis_variant:
            return restored

        restored = _restore_missing_y_before_plus_m(
            surface=surface,
            analysis_variant=analysis_variant,
        )
        if restored != analysis_variant:
            return restored

        restored = _restore_missing_nominal_suffix_from_surface(
            surface=surface,
            analysis_variant=analysis_variant,
            pos_variant=pos_variant,
        )
        if restored != analysis_variant:
            return restored

        restored = _restore_plain_nominal_lemma_m_suffix(
            surface=surface,
            analysis_variant=analysis_variant,
            pos_variant=pos_variant,
        )
        if restored != analysis_variant:
            return restored

        restored = _restore_missing_single_surface_tail(
            surface=surface,
            analysis_variant=analysis_variant,
            pos_variant=pos_variant,
        )
        if restored != analysis_variant:
            return restored

        return analysis_variant


def _demote_t_equal_to_t(analysis_variant: str) -> str:
    """Rewrite feminine /t= to /t in sg/pl-ambiguous forms."""
    return re.sub(r"/t=(?=\s*$|[+;,])", "/t", analysis_variant)


def _restore_missing_single_surface_tail(
    *,
    surface: str,
    analysis_variant: str,
    pos_variant: str,
) -> str:
    value = (analysis_variant or "").strip()
    if not value or value == "?":
        return analysis_variant
    if "[" in value or "+" in value or "~" in value or "&" in value:
        return analysis_variant
    if value.startswith("/"):
        return analysis_variant
    if not _is_nominal_or_pronoun_pos(pos_variant):
        return analysis_variant

    surface_norm = normalize_surface(surface).lower()
    reconstructed = normalize_surface(reconstruct_surface_from_analysis(value)).lower()
    if not surface_norm or reconstructed == surface_norm:
        return analysis_variant
    if not surface_norm.startswith(reconstructed):
        return analysis_variant
    if len(surface_norm) != len(reconstructed) + 1:
        return analysis_variant

    tail = surface_norm[-1]
    if not _RESTORABLE_TAIL_RE.fullmatch(tail):
        return analysis_variant
    if tail == "m" and not _is_pronoun_pos(pos_variant):
        return analysis_variant

    if value.endswith("/"):
        candidate = f"{value[:-1]}&{tail}/"
    else:
        candidate = f"{value}&{tail}"
    if normalize_surface(reconstruct_surface_from_analysis(candidate)).lower() == surface_norm:
        return candidate
    return analysis_variant


def _is_nominal_or_pronoun_pos(pos_variant: str) -> bool:
    head = (pos_variant or "").split(",", 1)[0].strip().lower()
    if not head:
        return False
    if head.startswith("vb"):
        return False
    return (
        head.startswith("n.")
        or head.startswith("adj.")
        or head.startswith("num.")
        or head.startswith("pers. pn.")
        or head.startswith("dn")
        or head.startswith("pn")
        or head.startswith("tn")
        or head.startswith("gn")
        or head.startswith("mn")
        or head.startswith("rn")
    )


def _is_pronoun_pos(pos_variant: str) -> bool:
    return (pos_variant or "").split(",", 1)[0].strip().lower().startswith("pers. pn.")


def _is_nominal_like_pos(pos_variant: str) -> bool:
    if _is_pronoun_pos(pos_variant):
        return False
    head = (pos_variant or "").split(",", 1)[0].strip().lower()
    return head.startswith("n.") or head.startswith("adj.") or head.startswith("num.")


def _restore_missing_nominal_suffix_from_surface(
    *,
    surface: str,
    analysis_variant: str,
    pos_variant: str,
) -> str:
    value = (analysis_variant or "").strip()
    if not value or not _is_nominal_like_pos(pos_variant):
        return analysis_variant
    if "[" in value or "+" in value or "~" in value or "&" in value:
        return analysis_variant

    slash_match = re.match(r"^(.*?)(\([IVX]+\))?/$", value)
    if not slash_match:
        return analysis_variant

    host = slash_match.group(1) or ""
    homonym = slash_match.group(2) or ""
    surface_norm = normalize_surface(surface).lower()
    reconstructed = normalize_surface(reconstruct_surface_from_analysis(value)).lower()
    if not surface_norm or reconstructed == surface_norm:
        return analysis_variant

    # Direct nominal endings visible on the surface.
    if surface_norm.startswith(reconstructed) and len(surface_norm) == len(reconstructed) + 1:
        tail = surface_norm[-1]
        if tail in {"t", "m", "r"}:
            if tail == "m" and reconstructed.endswith("m"):
                return analysis_variant
            candidate = f"{value}{tail}"
            if (
                normalize_surface(reconstruct_surface_from_analysis(candidate)).lower()
                == surface_norm
            ):
                return candidate

    # Cases like bt(II)/ -> bht(II)/m where host allograph is visible on surface.
    if surface_norm.endswith("m") and len(surface_norm) > 1 and surface_norm[:-1] != reconstructed:
        candidate = f"{surface_norm[:-1]}{homonym}/m"
        if normalize_surface(reconstruct_surface_from_analysis(candidate)).lower() == surface_norm:
            return candidate

    # n-assimilation to t, e.g. ṯn(I)/ -> ṯ(n(I)/t for surface ṯt.
    if (
        reconstructed.endswith("n")
        and surface_norm == f"{reconstructed[:-1]}t"
        and host.endswith("n")
    ):
        candidate = f"{host[:-1]}(n{homonym}/t"
        if normalize_surface(reconstruct_surface_from_analysis(candidate)).lower() == surface_norm:
            return candidate

    return analysis_variant


def _restore_plain_nominal_lemma_m_suffix(
    *,
    surface: str,
    analysis_variant: str,
    pos_variant: str,
) -> str:
    value = (analysis_variant or "").strip()
    if not value or not _is_nominal_like_pos(pos_variant):
        return analysis_variant
    if "[" in value or "+" in value or "~" in value or "&" in value or "/" in value:
        return analysis_variant
    if not _PLAIN_LEMMA_ANALYSIS_RE.fullmatch(value):
        return analysis_variant

    surface_norm = normalize_surface(surface).lower()
    if not surface_norm.endswith("m"):
        return analysis_variant

    candidate = f"{value}/m"
    if normalize_surface(reconstruct_surface_from_analysis(candidate)).lower() == surface_norm:
        return candidate
    return analysis_variant


def _restore_hidden_weak_y_before_enclitic_m(
    *,
    surface: str,
    analysis_variant: str,
    pos_variant: str,
) -> str:
    value = (analysis_variant or "").strip()
    if not value or not (pos_variant or "").lower().startswith("vb"):
        return analysis_variant
    surface_norm = normalize_surface(surface).lower()
    if not surface_norm.endswith("m"):
        return analysis_variant

    for marker in ("y[~m", "y[/~m"):
        if marker not in value:
            continue
        head, tail = value.rsplit(marker, 1)
        candidate = f"{head}(y{marker[1:]}{tail}"
        if normalize_surface(reconstruct_surface_from_analysis(candidate)).lower() == surface_norm:
            return candidate
    return analysis_variant


def _restore_missing_y_before_plus_m(
    *,
    surface: str,
    analysis_variant: str,
) -> str:
    value = (analysis_variant or "").strip()
    if not value or "+m" not in value or "&y" in value:
        return analysis_variant
    candidate = value.replace("+m", "&y+m", 1)
    if (
        normalize_surface(reconstruct_surface_from_analysis(candidate)).lower()
        == normalize_surface(surface).lower()
    ):
        return candidate
    return analysis_variant
