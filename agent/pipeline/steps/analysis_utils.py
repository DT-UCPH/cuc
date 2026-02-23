"""Shared helpers for analysis/surface reconstruction in refinement steps."""

import re
from typing import List

_NORMALIZE_MAP = str.maketrans(
    {
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
        "ʿ": "ʕ",
        "ˤ": "ʕ",
    }
)

_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")


def normalize_surface(text: str) -> str:
    """Normalize surface text for robust comparisons."""
    return (text or "").translate(_NORMALIZE_MAP)


def reconstruct_surface_from_analysis(analysis: str) -> str:
    """Reconstruct expected surface letters from one analysis variant.

    Rules match the linter conventions:
    - `(X)` reconstructed lexeme-only letters are omitted from surface.
    - `&Y` contributes surface-only letter `Y`.
    - `(X&Y` contributes `Y`.
    - homonym tags `(I)/(II)/...` and wrappers/markers are ignored.
    """
    a = (analysis or "").strip()
    if not a:
        return ""

    out: List[str] = []
    i = 0
    n = len(a)
    while i < n:
        m_hom = re.match(r"\(([IV]+)\)", a[i:])
        if m_hom:
            i += len(m_hom.group(0))
            continue

        ch = a[i]

        if ch == ":":
            i += 1
            while i < n and re.match(r"[A-Za-z]", a[i]):
                i += 1
            continue

        if ch == "(":
            if i + 1 < n and _LETTER_RE.match(a[i + 1]):
                if i + 3 < n and a[i + 2] == "&" and _LETTER_RE.match(a[i + 3]):
                    out.append(a[i + 3])
                    i += 4
                    continue
                i += 2
                continue
            i += 1
            continue

        if ch == "&":
            if i + 1 < n and _LETTER_RE.match(a[i + 1]):
                out.append(a[i + 1])
                i += 2
                continue
            i += 1
            continue

        if ch in {"!", "]", "[", "/", "=", "+", "~", ",", ")"}:
            i += 1
            continue

        if _LETTER_RE.match(ch):
            out.append(ch)
        i += 1

    return "".join(out)
