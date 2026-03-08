"""Normalize late `&...` clitic tails on function words to canonical suffix notation."""

from __future__ import annotations

import re

from pipeline.steps.base import RefinementStep, TabletRow

_END_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"&h\+m(?:\(I\))?$"), "+hm"),
    (re.compile(r"&k\+m(?:\(I\))?$"), "+km"),
    (re.compile(r"&n\+h$"), "+nh"),
    (re.compile(r"&n\+y$"), "+ny"),
    (re.compile(r"&n\+k$"), "+nk"),
    (re.compile(r"&n\+n$"), "+nn"),
    (re.compile(r"&hm$"), "+hm"),
    (re.compile(r"&km$"), "+km"),
    (re.compile(r"&nh$"), "+nh"),
    (re.compile(r"&ny$"), "+ny"),
    (re.compile(r"&nk$"), "+nk"),
    (re.compile(r"&nn$"), "+nn"),
    (re.compile(r"&~m$"), "+m(I)"),
    (re.compile(r"&m$"), "+m(I)"),
    (re.compile(r"&h$"), "+h"),
    (re.compile(r"&k$"), "+k"),
    (re.compile(r"&n$"), "+n"),
    (re.compile(r"&y$"), "+y"),
    (re.compile(r"&t$"), "+t"),
)


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _is_function_word_pos(pos_variant: str) -> bool:
    head = ((pos_variant or "").split(",", 1)[0]).strip().lower()
    return head.startswith(("prep.", "adv.", "conj.", "functor", "det."))


def _rewrite_variant(analysis_variant: str, pos_variant: str) -> str:
    text = (analysis_variant or "").strip()
    if not text or "&" not in text or not _is_function_word_pos(pos_variant):
        return analysis_variant
    if "&y+" in text:
        # Keep hidden weak-y reconstructions like `b&y+m(I)` intact.
        return analysis_variant
    for pattern, replacement in _END_REPLACEMENTS:
        if pattern.search(text):
            return pattern.sub(replacement, text)
    return analysis_variant


class FunctionWordCliticNotationFixer(RefinementStep):
    """Convert function-word surface tails into canonical clitic notation."""

    @property
    def name(self) -> str:
        return "function-word-clitic-notation"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row
        pos_variants = _split_semicolon(row.pos)

        changed = False
        out: list[str] = []
        for index, variant in enumerate(analysis_variants):
            pos_variant = pos_variants[index] if index < len(pos_variants) else row.pos
            rewritten = _rewrite_variant(variant, pos_variant)
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
