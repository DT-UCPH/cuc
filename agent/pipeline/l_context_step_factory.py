"""Factories for legacy and spaCy-based `l`-context refinement strategies."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.l_body_compound_prep import LBodyCompoundPrepDisambiguator
from pipeline.steps.l_functor_vocative_context import LFunctorVocativeContextDisambiguator
from pipeline.steps.l_kbd_compound_prep import LKbdCompoundPrepDisambiguator
from pipeline.steps.l_negation_verb_context import LNegationVerbContextPruner
from pipeline.steps.l_preposition_bigram_context import LPrepositionBigramContextDisambiguator
from pipeline.steps.spacy_l_context import SpacyLContextDisambiguator


def build_legacy_l_context_steps() -> list[RefinementStep]:
    """Return the historical `l`-context chain used by the parser."""
    return [
        LNegationVerbContextPruner(),
        LFunctorVocativeContextDisambiguator(),
        LKbdCompoundPrepDisambiguator(),
        LBodyCompoundPrepDisambiguator(),
        LPrepositionBigramContextDisambiguator(),
    ]


def build_spacy_l_context_steps() -> list[RefinementStep]:
    """Return the integrated spaCy-based `l`-context strategy."""
    return [SpacyLContextDisambiguator()]
