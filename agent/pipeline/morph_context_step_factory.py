"""Factory helpers for the active spaCy-based morphology-context strategy."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_morph_context import SpacyMorphContextDisambiguator


def build_spacy_morph_context_steps() -> list[RefinementStep]:
    """Return the active spaCy-based morphology-context strategy."""
    return [SpacyMorphContextDisambiguator()]
