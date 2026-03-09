"""Factory helpers for the spaCy-based Ugaritic rule spikes."""

from __future__ import annotations

import spacy
from spacy.language import Language

# Import registers the component factory.
from spacy_ugaritic.components.formula_context import make_formula_context_resolver  # noqa: F401
from spacy_ugaritic.components.k_context import make_k_context_resolver  # noqa: F401
from spacy_ugaritic.components.l_context import make_l_context_resolver  # noqa: F401
from spacy_ugaritic.components.lexical_context import make_lexical_context_resolver  # noqa: F401
from spacy_ugaritic.components.morph_context import make_morph_context_resolver  # noqa: F401
from spacy_ugaritic.components.offering_context import make_offering_context_resolver  # noqa: F401
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


def create_ugaritic_formula_context_nlp() -> Language:
    return create_ugaritic_nlp("ugaritic_formula_context_resolver")


def create_ugaritic_offering_context_nlp() -> Language:
    return create_ugaritic_nlp("ugaritic_offering_context_resolver")


def create_ugaritic_baal_context_nlp() -> Language:
    ensure_extensions()
    nlp = spacy.blank("xx")
    nlp.add_pipe("ugaritic_lexical_context_resolver", config={"rule_groups": ["baal"]})
    return nlp


def create_ugaritic_mlk_context_nlp() -> Language:
    ensure_extensions()
    nlp = spacy.blank("xx")
    nlp.add_pipe("ugaritic_lexical_context_resolver", config={"rule_groups": ["mlk"]})
    return nlp


def create_ugaritic_ydk_context_nlp() -> Language:
    ensure_extensions()
    nlp = spacy.blank("xx")
    nlp.add_pipe("ugaritic_lexical_context_resolver", config={"rule_groups": ["ydk"]})
    return nlp


def create_ugaritic_morph_context_nlp() -> Language:
    return create_ugaritic_nlp("ugaritic_morph_context_resolver")
