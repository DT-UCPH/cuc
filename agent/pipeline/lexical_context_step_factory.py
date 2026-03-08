"""Factory helpers for the active spaCy-based lexical-context strategies."""

from __future__ import annotations

from pipeline.dulat_attestation_index import DulatAttestationIndex
from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_lexical_context import (
    SpacyBaalContextDisambiguator,
    SpacyYdkContextDisambiguator,
)


def build_spacy_baal_context_steps(
    attestation_index: DulatAttestationIndex | None = None,
) -> list[RefinementStep]:
    """Return the active spaCy-based `bʕl` lexical-context strategy."""
    return [SpacyBaalContextDisambiguator(attestation_index=attestation_index)]


def build_spacy_ydk_context_steps() -> list[RefinementStep]:
    """Return the active spaCy-based `ydk` lexical-context strategy."""
    return [SpacyYdkContextDisambiguator()]
