"""Factory helpers for the late quote-translation tie-breaker."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import RefinementStep
from pipeline.steps.spacy_quote_translation_context import SpacyQuoteTranslationDisambiguator


def build_spacy_quote_translation_steps(dulat_db: Path | None = None) -> list[RefinementStep]:
    """Return the active exact-citation quote-translation tie-breaker."""
    return [SpacyQuoteTranslationDisambiguator(dulat_db=dulat_db)]
