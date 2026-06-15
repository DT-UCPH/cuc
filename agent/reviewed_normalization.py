"""Normalization helpers for legacy reviewed morphology notation."""

from __future__ import annotations

import re

_HOMONYM_AFTER_SLASH_RE = re.compile(r"/\(([IV]+)\)")


def normalize_reviewed_analysis(analysis: str) -> str:
    """Normalize legacy reviewed morphology strings toward current CUC notation."""
    text = (analysis or "").strip()
    if not text:
        return text

    # Legacy reviewed files often use ʿ where current CUC analysis uses ˤ.
    text = text.replace("ʿ", "ˤ")

    # Legacy homonym markers sometimes follow the slash: `mlk/(I)` -> `mlk(I)/`.
    text = _HOMONYM_AFTER_SLASH_RE.sub(r"(\1)/", text)

    # Legacy reviewed files often leave the default prepositional l bare.
    if text == "l":
        return "l(I)"
    if text.startswith("l+") and not text.startswith("l(I)+"):
        return f"l(I){text[1:]}"

    # Legacy reviewed files sometimes leave the default `king` homonym bare.
    if text == "mlk/":
        return "mlk(I)/"
    if text == "il/":
        return "il(I)/"
    if text == "bn/":
        return "bn(I)/"

    # One legacy review row encodes the noun `rgm/` with a stray infinitive marker.
    if text == "!!rgm/":
        return "rgm/"

    # Legacy reviewed files occasionally overmark the imperative `kbd`.
    if text == "!!kbd[:d":
        return "kbd[:d"

    # Legacy reviewed files sometimes leave the feminine `eye` noun underspecified.
    if text == "ˤn/t":
        return "ˤn(I)/t="

    return text
