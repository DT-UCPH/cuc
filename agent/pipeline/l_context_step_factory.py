"""Factory helpers for the active spaCy-based `l`-context strategy."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_l_context import SpacyLContextDisambiguator


def build_spacy_l_context_steps() -> list[RefinementStep]:
    """Return the active spaCy-based `l`-context strategy."""
    return [SpacyLContextDisambiguator()]
