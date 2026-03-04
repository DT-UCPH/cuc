"""Rule-based spaCy component for `k`-context disambiguation."""

from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.config.k_functor_bigram_surfaces import K_FUNCTOR_VERB_BIGRAM_SURFACES
from spacy_ugaritic.types import Candidate


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: tuple[Candidate, ...]
    after: tuple[Candidate, ...]


def _is_k_iii_candidate(candidate: Candidate) -> bool:
    return candidate.analysis == "k(III)" and candidate.dulat == "k (III)"


def _first_comment(token: Token) -> str:
    candidates = token._.resolved_candidates or token._.candidates
    if not candidates:
        return ""
    return candidates[0].comment


def _canonical_k_iii(comment: str = "") -> Candidate:
    return Candidate(
        "k(III)",
        "k (III)",
        "Subordinating or completive functor",
        "when",
        comment=comment,
    )


def _keep_single_k_iii(token: Token) -> tuple[Candidate, ...]:
    matches = tuple(
        candidate for candidate in token._.resolved_candidates if _is_k_iii_candidate(candidate)
    )
    if matches:
        return (matches[0],)
    return (_canonical_k_iii(comment=_first_comment(token)),)


def _has_class(token: Token | None, label: str) -> bool:
    if token is None:
        return False
    return label in token._.coarse_classes


def _next_token(doc: Doc, index: int) -> Token | None:
    if index + 1 >= len(doc):
        return None
    return doc[index + 1]


class KContextResolver:
    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("k_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        for index, token in enumerate(doc):
            if token.text != "k":
                continue
            next_token = _next_token(doc, index)
            if next_token is None:
                continue
            if next_token.text not in K_FUNCTOR_VERB_BIGRAM_SURFACES:
                continue
            if not _has_class(next_token, "VERB"):
                continue
            self._replace(token, _keep_single_k_iii(token), f"force-k-iii-{next_token.text}", doc)
        return doc

    def _replace(
        self, token: Token, candidates: tuple[Candidate, ...], rule: str, doc: Doc
    ) -> None:
        before = token._.resolved_candidates
        if before == candidates:
            return
        token._.resolved_candidates = candidates
        doc.user_data["k_context_events"].append(ResolutionEvent(token.i, rule, before, candidates))


@Language.factory("ugaritic_k_context_resolver")
def make_k_context_resolver(nlp, name):
    return KContextResolver()
