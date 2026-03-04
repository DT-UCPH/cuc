"""Factories for legacy and spaCy-based offering-context refinement strategies."""

from __future__ import annotations

from pipeline.steps.base import RefinementStep
from pipeline.steps.offering_l_prep import OfferingListLPrepFixer
from pipeline.steps.spacy_offering_context import SpacyOfferingContextDisambiguator


def build_legacy_offering_context_steps() -> list[RefinementStep]:
    """Return the historical offering-context step used by the parser."""
    return [OfferingListLPrepFixer()]


def build_spacy_offering_context_steps() -> list[RefinementStep]:
    """Return the spaCy-based offering-context strategy."""
    return [SpacyOfferingContextDisambiguator()]
