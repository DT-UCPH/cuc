"""Decode parser analysis strings into explicit morphology hints."""

from __future__ import annotations

import re
from dataclasses import dataclass

_PREFIX_RE = re.compile(r"^(!!|!([^!]+)!)")
_STEM_RE = re.compile(r":(d|l|r|pass)(?=$|[+~/])")
_SUFFIX_AFTER_ROOT_RE = re.compile(r"\[(.*)$")


@dataclass(frozen=True)
class DecodedAnalysis:
    raw: str
    is_prefix_conjugation: bool = False
    is_infinitive: bool = False
    is_participle: bool = False
    prefix_marker: str = ""
    visible_suffix: str = ""
    stem_marker: str = ""
    has_nominal_slash: bool = False
    nominal_suffix: str = ""
    has_suffix: bool = False
    suffix_marker: str = ""
    has_enclitic: bool = False
    enclitic_marker: str = ""


_PREFIX_PERSON_MAP = {
    "y": ("3", "m.", "sg."),
    "n": ("1", "c.", "pl."),
    "t=": ("2", "m.", "sg."),
    "t==": ("2", "f.", "sg."),
    "t===": ("2", "m.", "pl."),
}


def decode_analysis(analysis: str) -> DecodedAnalysis:
    value = (analysis or "").strip()
    if not value:
        return DecodedAnalysis(raw=value)

    prefix_marker = ""
    is_prefix = False
    is_inf = False
    match = _PREFIX_RE.match(value)
    if match:
        token = match.group(1)
        if token == "!!":
            is_inf = True
        else:
            is_prefix = True
            prefix_marker = (match.group(2) or "").strip()

    stem_match = _STEM_RE.search(value)
    stem_marker = stem_match.group(1) if stem_match else ""

    suffix_payload = ""
    suffix_match = _SUFFIX_AFTER_ROOT_RE.search(value)
    if suffix_match:
        suffix_payload = (suffix_match.group(1) or "").strip()

    nominal_suffix = ""
    has_nominal_slash = "/" in value
    if "/" in value:
        nominal_suffix = value.split("/", 1)[1].split("+", 1)[0].split("~", 1)[0].strip()

    suffix_marker = ""
    has_suffix = "+" in value
    if has_suffix:
        suffix_marker = value.split("+", 1)[1].strip()

    enclitic_marker = ""
    has_enclitic = "~" in value
    if has_enclitic:
        enclitic_marker = value.split("~", 1)[1].strip()

    is_participle = value.endswith("[/") or value.endswith("[/~m") or value.endswith("[/~(m")

    return DecodedAnalysis(
        raw=value,
        is_prefix_conjugation=is_prefix,
        is_infinitive=is_inf,
        is_participle=is_participle and not is_inf,
        prefix_marker=prefix_marker,
        visible_suffix=suffix_payload,
        stem_marker=stem_marker,
        has_nominal_slash=has_nominal_slash,
        nominal_suffix=nominal_suffix,
        has_suffix=has_suffix,
        suffix_marker=suffix_marker,
        has_enclitic=has_enclitic,
        enclitic_marker=enclitic_marker,
    )


def explicit_prefix_features(decoded: DecodedAnalysis) -> tuple[str, str, str]:
    marker = decoded.prefix_marker
    if marker.startswith("(ʔ&") or marker.startswith("ʔ&"):
        return ("1", "c.", "sg.")
    return _PREFIX_PERSON_MAP.get(marker, ("", "", ""))


def explicit_suffix_conjugation_features(decoded: DecodedAnalysis) -> tuple[str, str, str]:
    suffix = decoded.visible_suffix
    if suffix.startswith(":w"):
        return ("3", "m.", "pl.")
    if suffix.startswith("t==="):
        return ("3", "f.", "sg.")
    if suffix.startswith("t=="):
        return ("2", "f.", "sg.")
    if suffix.startswith("t="):
        return ("2", "m.", "sg.")
    if suffix.startswith("tm"):
        return ("2", "c.", "pl.")
    if suffix.startswith("tn"):
        return ("2", "f.", "pl.")
    if suffix.startswith("t"):
        return ("1", "c.", "sg.")
    if suffix == "":
        return ("3", "m.", "sg.")
    return ("", "", "")
