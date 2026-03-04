"""Builders for structured feature bundles."""

from __future__ import annotations

from morph_features.types import FeatureBundle


def build_verbal_bundle(
    *,
    stem: str,
    form: str,
    person: str = "",
    gender: str = "",
    number: str = "",
    state: str = "",
    case: str = "",
    source: str = "",
    confidence: str = "",
    has_enclitic: bool = False,
    enclitic_type: str = "",
) -> FeatureBundle:
    return FeatureBundle(
        part_of_speech="vb",
        stem=stem,
        conjugation_or_form=form,
        person=person,
        gender=gender,
        number=number,
        state=state,
        case=case,
        source=source,
        confidence=confidence,
        has_enclitic=has_enclitic,
        enclitic_type=enclitic_type,
    )


def build_nominal_bundle(
    *,
    part_of_speech: str,
    gender: str = "",
    number: str = "",
    state: str = "",
    case: str = "",
    source: str = "",
    confidence: str = "",
    has_suffix: bool = False,
    suffix_person: str = "",
    suffix_gender: str = "",
    suffix_number: str = "",
) -> FeatureBundle:
    return FeatureBundle(
        part_of_speech=part_of_speech,
        gender=gender,
        number=number,
        state=state,
        case=case,
        source=source,
        confidence=confidence,
        has_suffix=has_suffix,
        suffix_person=suffix_person,
        suffix_gender=suffix_gender,
        suffix_number=suffix_number,
        is_construct=state == "cstr.",
    )
