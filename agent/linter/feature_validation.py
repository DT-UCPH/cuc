"""Validation helpers for inferable morphology features."""

from __future__ import annotations

import re

from morph_features.analysis_decoder import (
    decode_analysis,
    explicit_prefix_features,
    explicit_suffix_conjugation_features,
)

_NAME_CLASSES = ("DN", "PN", "RN", "TN", "GN", "MN")
_SPLIT_T_PLURAL_RE = re.compile(r"/t=(?=\s*$|[+;,~])")
_SPLIT_T_SINGULAR_RE = re.compile(r"/t(?=\s*$|[+;,~])")


def inferable_feature_issues(
    analysis: str,
    pos_field: str,
    surface: str = "",
    dulat: str = "",
) -> list[str]:
    return verbal_feature_issues(
        analysis,
        pos_field,
        surface=surface,
        dulat=dulat,
    ) + nominal_feature_issues(analysis, pos_field)


def verbal_feature_issues(
    analysis: str,
    pos_field: str,
    *,
    surface: str = "",
    dulat: str = "",
) -> list[str]:
    pos = pos_field or ""
    if "vb" not in pos.lower():
        return []
    if _is_journey_formula_ytn_plural_notation(
        analysis=analysis,
        pos_field=pos_field,
        surface=surface,
        dulat=dulat,
    ):
        return []

    decoded = decode_analysis(analysis)
    if "prefc." in pos:
        person, gender, number = explicit_prefix_features(decoded)
    elif "suffc." in pos:
        person, gender, number = explicit_suffix_conjugation_features(decoded)
    else:
        person = gender = number = ""

    missing: list[str] = []
    if person and person not in pos:
        missing.append(person)
    if gender and gender not in pos:
        missing.append(gender)
    if number and number not in pos:
        missing.append(number)
    if missing:
        return [
            "Verb POS is missing explicit morphology from analysis: " + " ".join(missing).strip()
        ]
    return []


def nominal_feature_issues(analysis: str, pos_field: str) -> list[str]:
    pos = pos_field or ""
    if not _is_nominal_pos(pos):
        return []

    has_t_plural_split = _SPLIT_T_PLURAL_RE.search(analysis) is not None
    has_t_singular_split = (
        not has_t_plural_split and _SPLIT_T_SINGULAR_RE.search(analysis) is not None
    )

    conflicts: list[str] = []
    if has_t_plural_split and "sg." in pos and "pl." not in pos:
        conflicts.append("'/t=' marks feminine plural but POS is singular")
    if has_t_singular_split and "pl." in pos and "sg." not in pos:
        conflicts.append("'/t' marks feminine singular but POS is plural")
    if conflicts:
        return ["Nominal POS conflicts with analysis: " + "; ".join(conflicts)]

    expected: list[str] = []
    if "/tm" in analysis and "du." not in pos:
        expected.append("du.")
    elif has_t_plural_split:
        if "f." not in pos:
            expected.append("f.")
        if "pl." not in pos:
            expected.append("pl.")
    if analysis.endswith("/m") and "pl." not in pos:
        expected.append("pl.")
    if "+" in analysis and "cstr." not in pos:
        expected.append("cstr.")
    if expected:
        return [
            "Nominal POS is missing explicit morphology from analysis: "
            + " ".join(dict.fromkeys(expected))
        ]
    return []


def _is_nominal_pos(pos: str) -> bool:
    return (
        pos.startswith("n.")
        or pos.startswith("adj.")
        or any(name_class in pos for name_class in _NAME_CLASSES)
    )


def _is_journey_formula_ytn_plural_notation(
    *,
    analysis: str,
    pos_field: str,
    surface: str,
    dulat: str,
) -> bool:
    pos = pos_field or ""
    return (
        (surface or "").strip() == "ytn"
        and (dulat or "").strip() == "/y-t-n/"
        and (analysis or "").strip() in {"!y!(ytn[", "ytn["}
        and "vb" in pos.lower()
        and "3 m. pl." in pos
        and ("prefc." in pos or "suffc." in pos)
    )
