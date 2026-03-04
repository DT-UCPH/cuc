"""Validation helpers for inferable morphology features."""

from __future__ import annotations

from morph_features.analysis_decoder import (
    decode_analysis,
    explicit_prefix_features,
    explicit_suffix_conjugation_features,
)

_NAME_CLASSES = ("DN", "PN", "RN", "TN", "GN", "MN")


def inferable_feature_issues(analysis: str, pos_field: str) -> list[str]:
    return verbal_feature_issues(analysis, pos_field) + nominal_feature_issues(analysis, pos_field)


def verbal_feature_issues(analysis: str, pos_field: str) -> list[str]:
    pos = pos_field or ""
    if "vb" not in pos.lower():
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

    expected: list[str] = []
    if "/tm" in analysis and "du." not in pos:
        expected.append("du.")
    elif "/t=" in analysis:
        if "f." not in pos:
            expected.append("f.")
        if "pl." not in pos:
            expected.append("pl.")
    elif "/t" in analysis and "f." not in pos:
        expected.append("f.")
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
