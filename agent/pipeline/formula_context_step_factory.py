"""Factories for legacy and spaCy-based formula-context refinement strategies."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.formula_bigram import FormulaBigramFixer
from pipeline.steps.formula_trigram import FormulaTrigramFixer
from pipeline.steps.spacy_formula_context import SpacyFormulaContextDisambiguator


def build_legacy_formula_context_steps() -> list[RefinementStep]:
    """Return the historical formula-context chain used by the parser."""
    return [
        FormulaTrigramFixer(),
        FormulaBigramFixer(),
    ]


def build_spacy_formula_context_steps() -> list[RefinementStep]:
    """Return the spaCy-based formula-context strategy."""
    return [SpacyFormulaContextDisambiguator()]
