"""Typed morphology feature payloads for parser completion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureBundle:
    """One fully or partially resolved morphology bundle."""

    part_of_speech: str
    lexeme_class: str = ""
    stem: str = ""
    conjugation_or_form: str = ""
    person: str = ""
    gender: str = ""
    number: str = ""
    state: str = ""
    case: str = ""
    voice: str = ""
    is_construct: bool = False
    has_suffix: bool = False
    suffix_person: str = ""
    suffix_gender: str = ""
    suffix_number: str = ""
    has_enclitic: bool = False
    enclitic_type: str = ""
    source: str = ""
    confidence: str = ""
    ambiguity_group: str = ""


@dataclass(frozen=True)
class NominalFeatures:
    """Nominal feature subset."""

    gender: str = ""
    number: str = ""
    state: str = ""
    case: str = ""
    nominal_type: str = ""


@dataclass(frozen=True)
class VerbalFeatures:
    """Verbal feature subset."""

    stem: str = ""
    form_class: str = ""
    person: str = ""
    gender: str = ""
    number: str = ""
    voice: str = ""


@dataclass(frozen=True)
class CompletedVariant:
    """A rewritten analysis variant with structured morphology."""

    analysis: str
    dulat: str
    gloss: str
    comment: str
    features: FeatureBundle
