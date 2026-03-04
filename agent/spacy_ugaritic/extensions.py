"""spaCy extension registration for Ugaritic rule-based spikes."""

from __future__ import annotations

from spacy.tokens import Doc, Token


def ensure_extensions() -> None:
    if not Token.has_extension("line_id"):
        Token.set_extension("line_id", default="")
    if not Token.has_extension("surface"):
        Token.set_extension("surface", default="")
    if not Token.has_extension("section_ref"):
        Token.set_extension("section_ref", default="")
    if not Token.has_extension("candidates"):
        Token.set_extension("candidates", default=())
    if not Token.has_extension("resolved_candidates"):
        Token.set_extension("resolved_candidates", default=())
    if not Token.has_extension("coarse_classes"):
        Token.set_extension("coarse_classes", default=frozenset())
    if not Token.has_extension("line_index"):
        Token.set_extension("line_index", default=-1)
    if not Token.has_extension("row"):
        Token.set_extension("row", default=None)
    if not Token.has_extension("resolved_row"):
        Token.set_extension("resolved_row", default=None)
    if not Doc.has_extension("source_name"):
        Doc.set_extension("source_name", default="")
