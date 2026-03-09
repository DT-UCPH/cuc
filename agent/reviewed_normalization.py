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

    # Legacy infinitive notation often omits the trailing slash after `[`.
    if text.startswith("!!") and text.endswith("[") and not text.endswith("[/"):
        text = f"{text}/"

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

    return text
