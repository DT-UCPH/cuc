"""Factory helpers for the spaCy-based Ugaritic rule spikes."""

from __future__ import annotations

import spacy
from spacy.language import Language

# Import registers the component factory.
from spacy_ugaritic_components.l_context import make_l_context_resolver  # noqa: F401
from spacy_ugaritic_extensions import ensure_extensions


def create_ugaritic_nlp() -> Language:
    ensure_extensions()
    nlp = spacy.blank("xx")
    nlp.add_pipe("ugaritic_l_context_resolver")
    return nlp
