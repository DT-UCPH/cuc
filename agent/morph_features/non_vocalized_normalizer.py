"""Helpers for normalizing vocalized/reconstructed Ugaritic to parser surfaces."""

from __future__ import annotations

import re

_VOWEL_RE = re.compile(r"[aeiouāīūêôəAEIOUĀĪŪÊÔƏ]")
_DIACRITIC_RE = re.compile(r"[\u0300-\u036fV̆̄]")
_OPTION_RE = re.compile(r"[*/?.,()\[\]{}<>]")
_DIGIT_PLACEHOLDER_RE = re.compile(r"[123]")
_SLASH_ALT_RE = re.compile(r"/")
_ALEPH_VARIANTS = str.maketrans({"ả": "ʔ", "ỉ": "ʔ", "ủ": "ʔ", "ˀ": "ʔ", "ʾ": "ʔ"})


def normalize_vocalized_form(text: str) -> str:
    """Normalize a reconstructed transliteration to a comparable consonantal surface."""
    value = (text or "").strip()
    if not value or value == "?":
        return ""
    value = value.translate(_ALEPH_VARIANTS)
    value = _SLASH_ALT_RE.sub("", value)
    value = _OPTION_RE.sub("", value)
    value = _DIACRITIC_RE.sub("", value)
    value = _VOWEL_RE.sub("", value)
    value = _DIGIT_PLACEHOLDER_RE.sub("", value)
    return value.strip()
