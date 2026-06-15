"""Factory helpers for the active spaCy-based `k`-context strategy."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_k_context import SpacyKContextDisambiguator


def build_spacy_k_context_steps(dulat_db: Path | None = None) -> list[RefinementStep]:
    """Return the active spaCy-based `k`-context strategy."""
    return [SpacyKContextDisambiguator(dulat_db=dulat_db)]
