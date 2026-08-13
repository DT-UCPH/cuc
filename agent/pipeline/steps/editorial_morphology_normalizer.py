"""Remove sign-level editorial deletions from final morphology encodings."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow

_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_HOMONYM_RE = re.compile(r"\(([IVX]+)\)")


@dataclass(frozen=True)
class _SurfaceAtom:
    letter: str
    start: int
    end: int
    surface_only: bool


def _surface_atoms(analysis: str) -> list[_SurfaceAtom]:
    """Return output letters and their source slices in one analysis."""
    value = analysis or ""
    atoms: list[_SurfaceAtom] = []
    i = 0
    while i < len(value):
        if value.startswith("(]n]", i):
            i += 4
            continue
        homonym = _HOMONYM_RE.match(value, i)
        if homonym:
            i = homonym.end()
            continue
        if value.startswith(":pass", i):
            i += 5
            continue
        if any(value.startswith(marker, i) for marker in (":d", ":l", ":r", ":w", ":n")):
            i += 2
            continue
        if value[i] == "(":
            if i + 1 < len(value) and _LETTER_RE.match(value[i + 1]):
                if (
                    i + 3 < len(value)
                    and value[i + 2] == "&"
                    and _LETTER_RE.match(value[i + 3])
                ):
                    atoms.append(_SurfaceAtom(value[i + 3], i, i + 4, False))
                    i += 4
                    continue
                i += 2
                continue
        if value[i] == "&" and i + 1 < len(value) and _LETTER_RE.match(value[i + 1]):
            atoms.append(_SurfaceAtom(value[i + 1], i, i + 2, True))
            i += 2
            continue
        if _LETTER_RE.match(value[i]):
            atoms.append(_SurfaceAtom(value[i], i, i + 1, False))
        i += 1
    return atoms


def normalize_analysis_to_edited_reading(analysis: str, edited_surface: str) -> str | None:
    """Drop only ``&X`` atoms deleted by the sign-level editorial reading."""
    value = (analysis or "").strip()
    if not value or value == "?":
        return value
    atoms = _surface_atoms(value)
    target = normalize_surface(edited_surface)
    target_index = 0
    removals: list[tuple[int, int]] = []
    for atom in atoms:
        letter = normalize_surface(atom.letter)
        if target_index < len(target) and letter == target[target_index]:
            target_index += 1
            continue
        if not atom.surface_only:
            return None
        removals.append((atom.start, atom.end))
    if target_index != len(target):
        return None
    for start, end in reversed(removals):
        value = value[:start] + value[end:]
    if normalize_surface(reconstruct_surface_from_analysis(value)) != target:
        return None
    return value


class EditorialMorphologyNormalizer(RefinementStep):
    """Make final automatic analyses target the edited linguistic word."""

    @property
    def name(self) -> str:
        return "editorial-morphology-normalizer"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if row.analysis_surface == row.surface:
            return row
        normalized = normalize_analysis_to_edited_reading(row.analysis, row.analysis_surface)
        if normalized is None or normalized == row.analysis:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=normalized,
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )
