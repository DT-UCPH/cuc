"""Explicit English cue words for conservative `l` homonym translation hints."""

from __future__ import annotations

L_NEGATION_TRANSLATION_CUES = frozenset(
    {
        "not",
        "no",
        "without",
        "cannot",
        "don't",
        "dont",
        "didn't",
        "didnt",
        "hasn't",
        "hasnt",
        "hadn't",
        "hadnt",
        "never",
        "neither",
        "nor",
    }
)

L_CERTAINTY_TRANSLATION_CUES = frozenset(
    {
        "certainly",
        "undoubtedly",
        "truly",
        "really",
        "yes",
        "verily",
        "indeed",
    }
)

L_INTERJECTION_TRANSLATION_CUES = frozenset(
    {
        "oh",
    }
)
