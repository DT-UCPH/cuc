"""Factory helpers for the spaCy-based Ugaritic rule spikes."""

from __future__ import annotations

import spacy
from spacy.language import Language

# Import registers the component factory.
from spacy_ugaritic.components.k_context import make_k_context_resolver  # noqa: F401
from spacy_ugaritic.components.l_context import make_l_context_resolver  # noqa: F401
from spacy_ugaritic.extensions import ensure_extensions


def create_ugaritic_nlp(*component_names: str) -> Language:
    ensure_extensions()
    nlp = spacy.blank("xx")
    names = component_names or ("ugaritic_l_context_resolver",)
    for component_name in names:
        nlp.add_pipe(component_name)
    return nlp


def create_ugaritic_l_context_nlp() -> Language:
    return create_ugaritic_nlp("ugaritic_l_context_resolver")


def create_ugaritic_k_context_nlp() -> Language:
    return create_ugaritic_nlp("ugaritic_k_context_resolver")
