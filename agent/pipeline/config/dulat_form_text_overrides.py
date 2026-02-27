"""Overrides for known DULAT form-text parsing inconsistencies."""

from __future__ import annotations

import re

LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)


def _norm_text(value: str) -> str:
    return (value or "").strip().translate(LOOKUP_NORMALIZE).lower()


def _norm_homonym(value: str) -> str:
    return (value or "").strip().upper()


_FORM_TEXT_ALIAS_OVERRIDES: dict[tuple[str, str, str], tuple[str, ...]] = {
    # /l-s-m/: DULAT form-table parser stores `tslmn`, while attested surface
    # and lexical description use `tlsmn`.
    ("/l-s-m/", "", "tslmn"): ("tlsmn",),
}

_PREFORMATIVE_LETTERS = frozenset({"y", "t", "a", "n", "i", "u"})
_WEAK_FINAL_RADICALS = frozenset({"y", "w"})
_LEMMA_SEGMENT_RE = re.compile(r"\([^)]*\)")


def _weak_final_prefixed_aliases(lemma: str, form_text: str) -> tuple[str, ...]:
    """Expand weak-final prefixed forms where final radical may be unexpressed."""
    lemma_src = (lemma or "").strip()
    form_src = (form_text or "").strip()
    if not lemma_src or not form_src:
        return tuple()
    if not (lemma_src.startswith("/") and lemma_src.endswith("/")):
        return tuple()
    if form_src[0] not in _PREFORMATIVE_LETTERS:
        return tuple()

    body = _LEMMA_SEGMENT_RE.sub("", lemma_src[1:-1])
    parts = [part for part in body.split("-") if part]
    if len(parts) != 3:
        return tuple()
    final_radical = parts[-1]
    if final_radical not in _WEAK_FINAL_RADICALS:
        return tuple()
    if not form_src.endswith(final_radical):
        return tuple()

    alias = form_src[: -len(final_radical)]
    if len(alias) < 2:
        return tuple()
    return (alias,)


def expand_dulat_form_texts(
    *,
    lemma: str,
    homonym: str,
    form_text: str,
) -> tuple[str, ...]:
    """Return source form text plus any curated alias overrides."""
    source = (form_text or "").strip()
    if not source:
        return tuple()
    key = (_norm_text(lemma), _norm_homonym(homonym), _norm_text(source))
    aliases = _FORM_TEXT_ALIAS_OVERRIDES.get(key, tuple())
    dynamic_aliases = _weak_final_prefixed_aliases(lemma=lemma, form_text=source)
    out: list[str] = [source]
    for alias in (*aliases, *dynamic_aliases):
        value = (alias or "").strip()
        if value and value not in out:
            out.append(value)
    return tuple(out)
