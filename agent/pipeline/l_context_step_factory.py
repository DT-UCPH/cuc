"""Factory helpers for the active spaCy-based `l`-context strategy."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_l_context import SpacyLContextDisambiguator


def build_spacy_l_context_steps(dulat_db: Path | None = None) -> list[RefinementStep]:
    """Return the active spaCy-based `l`-context strategy."""
    return [SpacyLContextDisambiguator(dulat_db=dulat_db)]
