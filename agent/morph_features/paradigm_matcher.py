"""Paradigm helpers backed by linter.morphology tables."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from functools import lru_cache

from linter import morphology as ug_morphology
from morph_features.non_vocalized_normalizer import normalize_vocalized_form


@dataclass(frozen=True)
class ParadigmMatch:
    surface_non_vocalized: str
    analysis_signature: str
    feature_bundle: tuple[str, ...]


@lru_cache(maxsize=1)
def load_paradigm_matches() -> tuple[ParadigmMatch, ...]:
    out: list[ParadigmMatch] = []
    for name, value in vars(ug_morphology).items():
        if not name.startswith("paradigm_") or not isinstance(value, str):
            continue
        reader = csv.reader(io.StringIO(value), delimiter="\t")
        rows = [row for row in reader if row]
        if len(rows) < 2:
            continue
        headers = [cell.strip() for cell in rows[1]]
        for row in rows[2:]:
            cells = [cell.strip() for cell in row]
            if len(cells) < len(headers):
                continue
            record = dict(zip(headers, cells, strict=False))
            translit = record.get("translit", "")
            if not translit or translit == "?":
                continue
            out.append(
                ParadigmMatch(
                    surface_non_vocalized=normalize_vocalized_form(translit),
                    analysis_signature=name,
                    feature_bundle=tuple(
                        cell
                        for cell in [
                            record.get("pos", ""),
                            record.get("stem", ""),
                            record.get("conjugation", ""),
                            record.get("form", ""),
                            record.get("state", ""),
                            record.get("case", ""),
                        ]
                        if cell
                    ),
                )
            )
    return tuple(out)


def match_non_vocalized_paradigms(surface: str) -> list[ParadigmMatch]:
    normalized = normalize_vocalized_form(surface)
    if not normalized:
        return []
    return [match for match in load_paradigm_matches() if match.surface_non_vocalized == normalized]
