"""Derive edited linguistic readings from KTU editorial sign spans."""

from __future__ import annotations

import re
from pathlib import Path

_LETTER_RE = re.compile(r"[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ]")
_EXCISED_RE = re.compile(r"\[\[[^\]]*\]\]")
_REDUNDANT_RE = re.compile(r"\{[^}]*\}")
_EDITED_READING_RE = re.compile(
    r"(?:^|\|)\s*(?:Edited reading|KTU corrected):\s*([^|;\t]+)"
)
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


def edited_reading_surface(surface: str, sign_span: str) -> str | None:
    """Return the word after the sign-span editorial operations are applied.

    ``[[...]]`` (erased) and ``{...}`` (redundant) material is removed.
    Restored ``[...]`` and supplied ``<...>`` material remains.  ``None``
    means that the span cannot safely be aligned to the token or does not
    change its linguistic reading; an empty string is a valid result for a
    wholly erased token.
    """
    span = sign_span or ""
    if "[[" not in span and "{" not in span:
        return None
    if _normalized_letters(span) != _normalized_letters(surface):
        return None

    edited_markup = _EXCISED_RE.sub("", span)
    edited_markup = _REDUNDANT_RE.sub("", edited_markup)
    edited = _letters(edited_markup)
    if _normalized_letters(edited) == _normalized_letters(surface):
        return None
    return edited


def edited_reading_from_annotation(annotation: str) -> str | None:
    """Extract an internal edited-reading target from automatic TSV notes."""
    match = _EDITED_READING_RE.search(annotation or "")
    if not match:
        return None
    return _letters(match.group(1))


def analysis_target_surface(
    surface: str,
    *,
    annotation: str = "",
    sign_span: str = "",
) -> str:
    """Return the edited word that morphology is required to reconstruct."""
    from_span = edited_reading_surface(surface, sign_span) if sign_span else None
    if from_span is not None:
        return from_span
    from_annotation = edited_reading_from_annotation(annotation)
    if from_annotation is not None:
        return from_annotation
    return surface


def corrected_editorial_lookup_surface(surface: str, sign_span: str) -> str | None:
    """Return a safe corrected-reading alias for `[[...]]` and `{...}`.

    Excised and redundant signs occur in ``surface`` but are excluded from the
    corrected lexical reading. Missing ``<...>`` and restored ``[...]`` signs
    remain in the normalized reading and do not create aliases here.
    """
    span = sign_span or ""
    corrected = edited_reading_surface(surface, span)
    if corrected is None:
        return None

    # Parenthetical remarks and internal word dividers are heterogeneous.
    # Refuse to infer a single lexical token from them automatically.
    if "(" in span or ")" in span or "." in span:
        return None
    if len(_normalized_letters(corrected)) < 2:
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


def load_edited_reading_overrides(path: Path) -> dict[str, str]:
    """Load every safely changed token ID to its edited linguistic reading."""
    overrides: dict[str, str] = {}
    ambiguous_ids: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 4:
            continue
        line_id = (parts[0] or "").strip()
        if not line_id:
            continue
        edited = edited_reading_surface(parts[1] or "", parts[3] or "")
        if edited is None:
            continue
        previous = overrides.get(line_id)
        if previous is not None and previous != edited:
            ambiguous_ids.add(line_id)
            continue
        overrides[line_id] = edited
    for line_id in ambiguous_ids:
        overrides.pop(line_id, None)
    return overrides
