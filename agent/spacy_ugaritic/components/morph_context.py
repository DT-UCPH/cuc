"""Rule-based spaCy component for morphology-context pruning."""

from __future__ import annotations

import re
from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from spacy_ugaritic.types import Candidate

_CASE_RE = re.compile(r"(?<!\w)(nom\.|gen\.|acc\.|acc\.\?)(?!\w)")
_NAME_CLASSES = ("DN", "PN", "RN", "TN", "GN", "MN")


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
                agreement_token = _nearest_previous_plural_dual_subject(doc, index)
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
        for index, token in enumerate(doc):
            if not _is_preposition_token(token):
                continue
            for dependent in _following_genitive_targets(doc, index):
                rewritten = tuple(
                    _force_genitive(candidate) for candidate in dependent._.resolved_candidates
                )
                if rewritten != tuple(dependent._.resolved_candidates):
                    self._maybe_replace(
                        dependent,
                        rewritten,
                        "preposition-governs-genitive",
                    )
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
        if not _is_transparent_context_token(token):
            break
    return None


def _nearest_previous_plural_dual_subject(doc: Doc, index: int) -> Token | None:
    for lookback in range(1, 4):
        probe = index - lookback
        if probe < 0:
            break
        token = doc[probe]
        if _is_plural_dual_masculine_nominal(token):
            return token
        if not _is_transparent_context_token(token):
            break
    return None


def _is_all_verbal(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    return bool(candidates) and all("vb" in candidate.pos.lower() for candidate in candidates)


def _is_transparent_context_token(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    if not candidates:
        return False
    if _is_all_verbal(token):
        return True
    return all(_is_function_like(candidate) for candidate in candidates)


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


def _is_function_like(candidate: Candidate) -> bool:
    pos = candidate.pos.lower()
    return any(
        marker in pos
        for marker in (
            "prep.",
            "conj.",
            "functor",
            "adv.",
            "narrative adv.",
            "interr. pn.",
        )
    )


def _is_preposition_token(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    return bool(candidates) and all("prep." in candidate.pos.lower() for candidate in candidates)


def _following_genitive_targets(doc: Doc, index: int) -> tuple[Token, ...]:
    targets: list[Token] = []
    for lookahead in range(1, 4):
        probe = index + lookahead
        if probe >= len(doc):
            break
        token = doc[probe]
        if not _is_genitive_target_token(token):
            break
        targets.append(token)
    return tuple(targets)


def _is_genitive_target_token(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    return bool(candidates) and all(
        _candidate_accepts_genitive(candidate) for candidate in candidates
    )


def _candidate_accepts_genitive(candidate: Candidate) -> bool:
    pos = candidate.pos
    lowered = pos.lower()
    if "ptcpl." in lowered:
        return True
    if pos.startswith("n.") or pos.startswith("adj."):
        return True
    return any(name_class in pos for name_class in _NAME_CLASSES)


def _force_genitive(candidate: Candidate) -> Candidate:
    if not _candidate_accepts_genitive(candidate):
        return candidate
    pos = candidate.pos
    if _CASE_RE.search(pos):
        pos = _CASE_RE.sub("gen.", pos)
    else:
        pos = f"{pos} gen.".strip()
    return Candidate(
        analysis=candidate.analysis,
        dulat=candidate.dulat,
        pos=pos,
        gloss=candidate.gloss,
        comment=candidate.comment,
    )


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
