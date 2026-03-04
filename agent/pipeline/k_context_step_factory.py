"""Factories for legacy and spaCy-based `k`-context refinement strategies."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.k_functor_bigram_context import KFunctorBigramContextDisambiguator
from pipeline.steps.spacy_k_context import SpacyKContextDisambiguator


def build_legacy_k_context_steps() -> list[RefinementStep]:
    """Return the historical `k`-context step used by the parser."""
    return [KFunctorBigramContextDisambiguator()]


def build_spacy_k_context_steps() -> list[RefinementStep]:
    """Return the spaCy-based `k`-context strategy."""
    return [SpacyKContextDisambiguator()]
