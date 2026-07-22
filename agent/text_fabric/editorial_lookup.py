"""Derive conservative lexical lookup aliases from KTU editorial sign spans."""

from __future__ import annotations

import re
from pathlib import Path

_LETTER_RE = re.compile(r"[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ]")
_EXCISED_RE = re.compile(r"\[\[[^\]]*\]\]")
_REDUNDANT_RE = re.compile(r"\{[^}]*\}")
_NORMALIZE_MAP = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)


def _letters(value: str) -> str:
    return "".join(_LETTER_RE.findall(value or ""))


def _normalized_letters(value: str) -> str:
    return _letters(value).translate(_NORMALIZE_MAP)


def corrected_editorial_lookup_surface(surface: str, sign_span: str) -> str | None:
    """Return a safe corrected-reading alias for `[[...]]` and `{...}`.

    Excised and redundant signs occur in ``surface`` but are excluded from the
    corrected lexical reading. Missing ``<...>`` and restored ``[...]`` signs
    remain in the normalized reading and do not create aliases here.
    """
    span = sign_span or ""
    if "[[" not in span and "{" not in span:
        return None
    if _normalized_letters(span) != _normalized_letters(surface):
        return None

    corrected_markup = _EXCISED_RE.sub("", span)
    corrected_markup = _REDUNDANT_RE.sub("", corrected_markup)

    # Parenthetical remarks and internal word dividers are heterogeneous.
    # Refuse to infer a single lexical token from them automatically.
    if "(" in corrected_markup or ")" in corrected_markup or "." in corrected_markup:
        return None

    corrected = _letters(corrected_markup)
    if len(_normalized_letters(corrected)) < 2:
        return None
    if _normalized_letters(corrected) == _normalized_letters(surface):
        return None
    return corrected


def load_editorial_lookup_overrides(path: Path) -> dict[str, str]:
    """Load token-ID to corrected lexical lookup aliases from one raw TF TSV."""
    overrides: dict[str, str] = {}
    ambiguous_ids: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 4:
            continue
        line_id = (parts[0] or "").strip()
        surface = parts[1] or ""
        sign_span = parts[3] or ""
        if not line_id:
            continue
        corrected = corrected_editorial_lookup_surface(surface, sign_span)
        if corrected is None:
            continue
        previous = overrides.get(line_id)
        if previous is not None and previous != corrected:
            ambiguous_ids.add(line_id)
            continue
        overrides[line_id] = corrected
    for line_id in ambiguous_ids:
        overrides.pop(line_id, None)
    return overrides
