"""Keep L-stem geminated radicals inside the verbal stem (before `[`).

Legacy rows like `!t!qṭ[ṭ:l` split the doubled radical into the tail as if it
were an ending. For L stems, the doubled radical is part of the stem and
should be encoded before `[` (e.g. `!t!qṭṭ[:l`).
"""

from __future__ import annotations

import re

from pipeline.steps.analysis_utils import normalize_surface
from pipeline.steps.base import RefinementStep, TabletRow

_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)
_VERBAL_NOUN_POS_RE = re.compile(r"\bvb\.\s*n\.", flags=re.IGNORECASE)
_POS_L_STEM_RE = re.compile(r"\b(L|Lt|tL)\b")
_ANALYSIS_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_LEADING_TAIL_LETTERS_RE = re.compile(r"^([A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+)(.*)$")


def _split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def _analysis_letters(text: str) -> str:
    return "".join(ch for ch in (text or "") if _ANALYSIS_LETTER_RE.match(ch))


def _is_l_stem_verb_pos(pos_text: str) -> bool:
    if not _VB_POS_HEAD_RE.search(pos_text or ""):
        return False
    if _VERBAL_NOUN_POS_RE.search(pos_text or ""):
        return False
    return bool(_POS_L_STEM_RE.search(pos_text or ""))


def _promote_leading_tail_letter_to_stem(surface: str, analysis_variant: str) -> str:
    value = (analysis_variant or "").strip()
    if not value or "[" not in value:
        return analysis_variant
    if "[/" in value:
        return analysis_variant

    head, tail = value.split("[", 1)
    match = _LEADING_TAIL_LETTERS_RE.match(tail or "")
    if not match:
        return analysis_variant
    leading, remainder = match.groups()
    if not leading:
        return analysis_variant

    head_letters = _analysis_letters(head)
    if len(head_letters) < 2:
        return analysis_variant

    last_stem_letter = head_letters[-1]
    # Already geminated in the stem body; keep suffix letters after `[` intact.
    if len(head_letters) >= 2 and head_letters[-2] == last_stem_letter:
        return analysis_variant

    if leading[0] != last_stem_letter:
        return analysis_variant

    surface_letters = _analysis_letters(normalize_surface(surface))
    if not surface_letters.startswith(head_letters + leading[0]):
        return analysis_variant

    # Move exactly one repeated radical into the stem.
    return f"{head}{leading[0]}[{leading[1:]}{remainder}"


class VerbLStemGeminationFixer(RefinementStep):
    """Normalize L-stem doubled radical placement around `[`."""

    @property
    def name(self) -> str:
        return "verb-l-stem-gemination"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if not _is_l_stem_verb_pos(row.pos or ""):
            return row

        variants = _split_semicolon(row.analysis)
        if not variants:
            return row

        changed = False
        out_variants: list[str] = []
        for variant in variants:
            rewritten = _promote_leading_tail_letter_to_stem(row.surface, variant)
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
