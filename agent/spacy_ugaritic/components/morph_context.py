"""Rule-based spaCy component for morphology-context pruning."""

from __future__ import annotations

from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from spacy_ugaritic.types import Candidate


@dataclass(frozen=True)
class MorphResolutionEvent:
    token_index: int
    rule: str
    before: tuple[Candidate, ...]
    after: tuple[Candidate, ...]


class MorphContextResolver:
    """Prune ambiguous morphology bundles using local agreement cues."""

    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("morph_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        for index, token in enumerate(doc):
            if not _has_multiple_verbal_png(token):
                continue
            agreement_token = _nearest_plural_dual_subject(doc, index)
            if agreement_token is None:
                continue
            keep_numbers = _subject_numbers(agreement_token)
            filtered = tuple(
                candidate
                for candidate in token._.resolved_candidates
                if _is_third_masculine_for_numbers(candidate, keep_numbers)
            )
            if filtered:
                self._maybe_replace(token, filtered, "plural-dual-subject-agreement")
        return doc

    def _maybe_replace(
        self,
        token: Token,
        candidates: tuple[Candidate, ...],
        rule: str,
    ) -> None:
        before = tuple(token._.resolved_candidates)
        if candidates == before:
            return
        token._.resolved_candidates = candidates
        token.doc.user_data["morph_context_events"].append(
            MorphResolutionEvent(token.i, rule, before, candidates)
        )


def _has_multiple_verbal_png(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    if len(candidates) < 2:
        return False
    verb_candidates = [candidate for candidate in candidates if "vb" in candidate.pos.lower()]
    if len(verb_candidates) < 2:
        return False
    png_values = {(candidate.pos, candidate.analysis) for candidate in verb_candidates}
    return len(png_values) > 1


def _nearest_plural_dual_subject(doc: Doc, index: int) -> Token | None:
    for lookahead in range(1, 3):
        probe = index + lookahead
        if probe >= len(doc):
            break
        token = doc[probe]
        if _is_plural_dual_masculine_nominal(token):
            return token
        if not _is_all_verbal(token):
            break
    return None


def _is_all_verbal(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    return bool(candidates) and all("vb" in candidate.pos.lower() for candidate in candidates)


def _is_plural_dual_masculine_nominal(token: Token) -> bool:
    return bool(_subject_numbers(token))


def _subject_numbers(token: Token) -> set[str]:
    keep_numbers: set[str] = set()
    for candidate in token._.resolved_candidates:
        pos = candidate.pos
        if "n. m." not in pos and "adj. m." not in pos:
            continue
        if "pl." in pos or "tant." in pos:
            keep_numbers.add("pl.")
        if "du." in pos or "tant." in pos:
            keep_numbers.add("du.")
    return keep_numbers


def _is_third_masculine_for_numbers(candidate: Candidate, keep_numbers: set[str]) -> bool:
    pos = candidate.pos
    return (
        "vb" in pos.lower()
        and "3" in pos
        and "m." in pos
        and any(number in pos for number in keep_numbers)
    )


@Language.factory("ugaritic_morph_context_resolver")
def make_morph_context_resolver(nlp, name):
    return MorphContextResolver()
