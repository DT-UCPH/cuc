"""Factory helpers for the active spaCy-based `k`-context strategy."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_k_context import SpacyKContextDisambiguator


def build_spacy_k_context_steps() -> list[RefinementStep]:
    """Return the active spaCy-based `k`-context strategy."""
    return [SpacyKContextDisambiguator()]
