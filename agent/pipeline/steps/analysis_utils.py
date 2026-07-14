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


def analysis_matches_surface(surface: str, analysis: str) -> bool:
    """Return whether an analysis is compatible with one written surface.

    Besides exact reconstruction, this also accepts verbal plural ``:w`` as an
    implicit ending. In Ugaritic that plural marker is often not written, even
    though the project encoding represents it explicitly.
    """
    surface_norm = normalize_surface(surface)
    reconstructed_norm = normalize_surface(reconstruct_surface_from_analysis(analysis))
    if reconstructed_norm == surface_norm:
        return True
    if ":w" not in (analysis or ""):
        return False
    return reconstructed_norm == f"{surface_norm}w"


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
        if a.startswith("(]n]", i):
            i += 4
            continue

        m_hom = re.match(r"\(([IV]+)\)", a[i:])
        if m_hom:
            i += len(m_hom.group(0))
            continue

        ch = a[i]

        if a.startswith(":pass", i):
            i += len(":pass")
            continue
        if (
            a.startswith(":d", i)
            or a.startswith(":l", i)
            or a.startswith(":r", i)
            or a.startswith(":w", i)
            or a.startswith(":n", i)
        ):
            # Stem labels plus the unwritten-ending markers ':w' (plural -u)
            # and ':n'; kept in sync with linter.lint's decoder.
            i += 2
            continue
        if ch == ":":
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
