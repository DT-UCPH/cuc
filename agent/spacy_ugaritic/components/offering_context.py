"""Rule-based spaCy component for offering-list `l` preposition normalization."""

from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.steps.dulat_gate import LOOKUP_NORMALIZE
from spacy_ugaritic.types import Candidate

_OFFERING_SURFACES = {
    "gdlt",
    "alp",
    "alpm",
    "šnpt",
    "ʕr",
    "npš",
    "ššrt",
    "š",
    "ynt",
}


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: Candidate
    after: Candidate


def _normalize(text: str) -> str:
    return (text or "").translate(LOOKUP_NORMALIZE).strip()


def _is_nominal_pos(pos_text: str) -> bool:
    pos = (pos_text or "").strip()
    if not pos:
        return False
    return any(tag in pos for tag in ("n.", "adj.", "num.", "DN", "PN", "TN"))


def _is_ambiguous_l_candidate(surface: str, candidate: Candidate) -> bool:
    return (
        surface.strip() == "l"
        and candidate.analysis.strip() == "l(I);l(II);l(III)"
        and candidate.dulat.strip() == "l (I);l (II);l (III)"
        and candidate.pos.strip() == "prep.;adv.;functor"
        and candidate.gloss.strip() == "to;no;certainly"
    )


def _is_offering_candidate(surface: str, candidate: Candidate) -> bool:
    return _normalize(surface) in _OFFERING_SURFACES and _is_nominal_pos(candidate.pos)


def _is_recipient_candidate(candidate: Candidate) -> bool:
    if "vb" in (candidate.pos or "").strip():
        return False
    return _is_nominal_pos(candidate.pos)


def _canonical_l_prep(candidate: Candidate) -> Candidate:
    return Candidate(
        analysis="l(I)",
        dulat="l (I)",
        pos="prep.",
        gloss="to",
        comment=candidate.comment,
    )


def _resolved_candidate(token: Token) -> Candidate | None:
    candidates = token._.resolved_candidates or token._.candidates
    if not candidates:
        return None
    return candidates[0]


class OfferingContextResolver:
    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("offering_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        snapshot = [_resolved_candidate(token) for token in doc]
        for index, token in enumerate(doc):
            candidate = snapshot[index]
            if candidate is None or candidate.is_unresolved():
                continue
            if not _is_ambiguous_l_candidate(token._.surface, candidate):
                continue
            if index == 0 or index + 1 >= len(doc):
                continue
            prev_candidate = snapshot[index - 1]
            next_candidate = snapshot[index + 1]
            if prev_candidate is None or next_candidate is None:
                continue
            if not _is_offering_candidate(doc[index - 1]._.surface, prev_candidate):
                continue
            if not _is_recipient_candidate(next_candidate):
                continue
            updated = _canonical_l_prep(candidate)
            token._.resolved_candidates = (updated,)
            doc.user_data["offering_context_events"].append(
                ResolutionEvent(index, "offering-l-prep", candidate, updated)
            )
        return doc


@Language.factory("ugaritic_offering_context_resolver")
def make_offering_context_resolver(nlp, name):
    return OfferingContextResolver()
