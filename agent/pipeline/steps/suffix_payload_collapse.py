"""Collapse suffix-linked DULAT/POS/gloss payload to host lexeme metadata."""

from __future__ import annotations

import re

from pipeline.steps.base import RefinementStep, TabletRow

_CLITIC_MARKER_RE = re.compile(r"(?:\+|~|\[)[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+=?")
_DULAT_SUFFIX_LINK_RE = re.compile(
    r",\s*-[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+=?\s*(?:\([IVX]+\))?=?",
    flags=re.IGNORECASE,
)
_POS_TAIL_KEYS = (
    "pers. pn",
    "suff. pn",
    "morph",
    "adv. functor",
    "postp.",
    "prep.",
    "emph. or det. encl.",
    "→",
)
_GLOSS_TAILS = {
    "",
    "my",
    "your",
    "your(s)",
    "his /her",
    "his /her (hers) / its",
    "our",
    "their",
    "me",
    "sun",
    "yes",
    "to",
    "und das (ist) so!",
}


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _has_clitic_marker(analysis_variant: str) -> bool:
    return bool(_CLITIC_MARKER_RE.search((analysis_variant or "").strip()))


def _has_dulat_suffix_payload(dulat_variant: str) -> bool:
    return bool(_DULAT_SUFFIX_LINK_RE.search((dulat_variant or "").strip()))


def _trim_pos_suffix_payload(pos_variant: str) -> str:
    parts = [part.strip() for part in (pos_variant or "").split(",")]
    while len(parts) > 1:
        tail = (parts[-1] or "").strip().lower()
        if not tail:
            parts.pop()
            continue
        if any(key in tail for key in _POS_TAIL_KEYS):
            parts.pop()
            continue
        break
    return ", ".join(parts).strip()


def _trim_gloss_suffix_payload(gloss_variant: str) -> str:
    parts = [part.strip() for part in (gloss_variant or "").split(",")]
    while len(parts) > 1:
        tail = (parts[-1] or "").strip().lower()
        if tail in _GLOSS_TAILS:
            parts.pop()
            continue
        break
    return ", ".join(parts).strip()


class SuffixPayloadCollapseFixer(RefinementStep):
    """For clitic-bearing analysis variants, keep host lexeme payload in cols 4-6."""

    @property
    def name(self) -> str:
        return "suffix-payload-collapse"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row

        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)
        gloss_variants = _split_semicolon(row.gloss)

        changed = False
        out_dulat: list[str] = []
        out_pos: list[str] = []
        out_gloss: list[str] = []

        max_len = max(
            len(analysis_variants),
            len(dulat_variants),
            len(pos_variants),
            len(gloss_variants),
        )
        for idx in range(max_len):
            a_var = analysis_variants[idx] if idx < len(analysis_variants) else ""
            d_var = dulat_variants[idx] if idx < len(dulat_variants) else ""
            p_var = pos_variants[idx] if idx < len(pos_variants) else ""
            g_var = gloss_variants[idx] if idx < len(gloss_variants) else ""

            d_new = d_var
            p_new = p_var
            g_new = g_var

            if _has_clitic_marker(a_var) and _has_dulat_suffix_payload(d_var):
                d_new = d_var.split(",", 1)[0].strip()
                p_new = _trim_pos_suffix_payload(p_var)
                g_new = _trim_gloss_suffix_payload(g_var)

            if d_new != d_var or p_new != p_var or g_new != g_var:
                changed = True

            out_dulat.append(d_new)
            out_pos.append(p_new)
            out_gloss.append(g_new)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=row.analysis,
            dulat="; ".join(out_dulat),
            pos="; ".join(out_pos),
            gloss="; ".join(out_gloss),
            comment=row.comment,
        )
