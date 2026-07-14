"""Remove noun-style '/' closure from pronouns and particles."""

from __future__ import annotations

import re

from pipeline.steps.base import RefinementStep, TabletRow

_TRAILING_SLASH_RE = re.compile(r"^(?P<lemma>[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+)(?P<hom>\([IVX]+\))?/$")


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


def _is_pronoun_like(pos_slot: str) -> bool:
    pos = (pos_slot or "").strip().lower()
    return "pn." in pos or "pron" in pos


class PronounClosureFixer(RefinementStep):
    """Normalize pronouns to no trailing closure marker."""

    @property
    def name(self) -> str:
        return "pronoun-closure"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row
        pos_variants = _split_semicolon(row.pos)

        changed = False
        out: list[str] = []
        for idx, variant in enumerate(analysis_variants):
            pos_slot = pos_variants[idx] if idx < len(pos_variants) else ""
            pos_head = _split_comma(pos_slot)[0] if pos_slot else ""
            rewritten = self._rewrite_variant(variant=variant, pos_head=pos_head)
            if rewritten != variant:
                changed = True
            out.append(rewritten)

        if not changed:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(out),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _rewrite_variant(self, variant: str, pos_head: str) -> str:
        value = (variant or "").strip()
        if not value or value == "?":
            return value
        if not _is_pronoun_like(pos_head):
            return value
        if any(ch in value for ch in ("+", "~", "[")):
            return value
        match = _TRAILING_SLASH_RE.match(value)
        if not match:
            return value
        lemma = (match.group("lemma") or "").strip()
        hom = (match.group("hom") or "").strip()
        return f"{lemma}{hom}"
