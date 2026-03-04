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
        source=source,
        confidence=confidence,
        has_enclitic=has_enclitic,
        enclitic_type=enclitic_type,
    )
