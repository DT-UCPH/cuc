"""Factory helpers for the active spaCy-based formula-context strategy."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_formula_context import SpacyFormulaContextDisambiguator


def build_spacy_formula_context_steps() -> list[RefinementStep]:
    """Return the active spaCy-based formula-context strategy."""
    return [SpacyFormulaContextDisambiguator()]
