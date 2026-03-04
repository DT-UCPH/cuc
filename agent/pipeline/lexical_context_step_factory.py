"""Factory helpers for the active spaCy-based lexical-context strategies."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_lexical_context import (
    SpacyBaalContextDisambiguator,
    SpacyYdkContextDisambiguator,
)


def build_spacy_baal_context_steps() -> list[RefinementStep]:
    """Return the active spaCy-based `bʕl` lexical-context strategy."""
    return [SpacyBaalContextDisambiguator()]


def build_spacy_ydk_context_steps() -> list[RefinementStep]:
    """Return the active spaCy-based `ydk` lexical-context strategy."""
    return [SpacyYdkContextDisambiguator()]
