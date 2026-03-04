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
            if index == 0 or not _is_second_singular_pronoun(doc[index - 1]):
                continue
            filtered = tuple(
                candidate
                for candidate in token._.resolved_candidates
                if _is_second_singular_verb_candidate(candidate)
            )
            if filtered:
                self._maybe_replace(token, filtered, "second-singular-pronoun-agreement")

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
            self._apply_post_preposition_sequence(doc, index)
        for start in range(len(doc) - 1):
            if _is_preposition_token(doc[start]):
                continue
            if start > 0 and (
                _is_construct_capable_token(doc[start - 1]) or _is_preposition_token(doc[start - 1])
            ):
                continue
            chain = _construct_chain_tokens(doc, start)
            if len(chain) < 2:
                continue
            self._apply_construct_chain(chain, governed_by_preposition=False)
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

    def _apply_post_preposition_sequence(self, doc: Doc, index: int) -> None:
        next_index = index + 1
        if next_index >= len(doc):
            return

        modifiers: list[Token] = []
        probe = next_index
        while probe < len(doc) and _is_modifier_token(doc[probe]):
            modifiers.append(doc[probe])
            probe += 1

        if probe >= len(doc):
            for modifier in modifiers:
                rewritten = _dedupe_candidates(
                    tuple(
                        _force_case(candidate, "gen.")
                        for candidate in modifier._.resolved_candidates
                    )
                )
                if rewritten != tuple(modifier._.resolved_candidates):
                    self._maybe_replace(modifier, rewritten, "preposition-governs-genitive")
            return
        head = doc[probe]
        if not _is_construct_capable_token(head):
            return

        for modifier in modifiers:
            rewritten = _dedupe_candidates(
                tuple(
                    _force_case(candidate, "gen.") for candidate in modifier._.resolved_candidates
                )
            )
            if rewritten != tuple(modifier._.resolved_candidates):
                self._maybe_replace(modifier, rewritten, "preposition-governs-genitive")

        chain = _construct_chain_tokens(doc, probe)
        if len(chain) >= 2:
            self._apply_construct_chain(chain, governed_by_preposition=True)
            return

        rewritten = _dedupe_candidates(
            tuple(
                _force_state_case(candidate, "abs.", "gen.")
                for candidate in head._.resolved_candidates
            )
        )
        if rewritten != tuple(head._.resolved_candidates):
            self._maybe_replace(head, rewritten, "preposition-governs-genitive")

    def _apply_construct_chain(
        self,
        chain: tuple[Token, ...],
        *,
        governed_by_preposition: bool,
    ) -> None:
        last_index = len(chain) - 1
        for index, token in enumerate(chain):
            if index == last_index:
                state = "abs."
                case = "gen."
            elif index == 0:
                state = "cstr."
                case = "gen." if governed_by_preposition else "nom."
            else:
                state = "cstr."
                case = "gen."
            rewritten = _dedupe_candidates(
                tuple(
                    _force_state_case(candidate, state, case)
                    for candidate in token._.resolved_candidates
                    if _candidate_accepts_construct_chain(candidate)
                )
            )
            if rewritten and rewritten != tuple(token._.resolved_candidates):
                self._maybe_replace(token, rewritten, "construct-chain-case")


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


def _is_second_singular_pronoun(token: Token) -> bool:
    for candidate in token._.resolved_candidates:
        pos = (candidate.pos or "").lower()
        analysis = candidate.analysis or ""
        dulat = candidate.dulat or ""
        if "pers. pn." not in pos:
            continue
        if analysis.startswith("at(I)") or dulat.startswith("ảt (I)"):
            return True
    return False


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


def _is_second_singular_verb_candidate(candidate: Candidate) -> bool:
    pos = candidate.pos or ""
    lowered = pos.lower()
    return "vb" in lowered and "2" in pos and "sg." in pos


def _is_preposition_token(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    return bool(candidates) and all("prep." in candidate.pos.lower() for candidate in candidates)


def _construct_chain_tokens(doc: Doc, start: int) -> tuple[Token, ...]:
    if start >= len(doc) or not _is_construct_capable_token(doc[start]):
        return ()
    chain: list[Token] = [doc[start]]
    probe = start
    while probe + 1 < len(doc):
        if not _token_supports_construct_head(doc[probe]):
            break
        next_token = doc[probe + 1]
        if not _is_construct_capable_token(next_token):
            break
        chain.append(next_token)
        probe += 1
    return tuple(chain)


def _is_construct_capable_token(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    return bool(candidates) and any(
        _candidate_accepts_construct_chain(candidate) for candidate in candidates
    )


def _token_supports_construct_head(token: Token) -> bool:
    return any(
        _candidate_supports_construct_head(candidate)
        for candidate in token._.resolved_candidates
        if _candidate_accepts_construct_chain(candidate)
    )


def _is_modifier_token(token: Token) -> bool:
    candidates = tuple(token._.resolved_candidates)
    return bool(candidates) and all(_candidate_is_modifier(candidate) for candidate in candidates)


def _candidate_accepts_construct_chain(candidate: Candidate) -> bool:
    pos = candidate.pos
    lowered = pos.lower()
    if "ptcpl." in lowered:
        return True
    if pos.startswith("n."):
        return True
    return any(name_class in pos for name_class in _NAME_CLASSES)


def _candidate_is_modifier(candidate: Candidate) -> bool:
    lowered = candidate.pos.lower()
    return lowered.startswith("adj.") or "ptcpl." in lowered


def _candidate_supports_construct_head(candidate: Candidate) -> bool:
    analysis = candidate.analysis.strip()
    if "+" in analysis:
        return True
    return analysis.endswith("/")


def _force_case(candidate: Candidate, case: str) -> Candidate:
    if not (_candidate_accepts_construct_chain(candidate) or _candidate_is_modifier(candidate)):
        return candidate
    pos = candidate.pos
    if _CASE_RE.search(pos):
        pos = _CASE_RE.sub(case, pos)
    else:
        pos = f"{pos} {case}".strip()
    return Candidate(
        analysis=candidate.analysis,
        dulat=candidate.dulat,
        pos=pos,
        gloss=candidate.gloss,
        comment=candidate.comment,
    )


def _force_state_case(candidate: Candidate, state: str, case: str) -> Candidate:
    if not _candidate_accepts_construct_chain(candidate):
        return candidate
    pos = candidate.pos
    parts = [
        part
        for part in pos.split()
        if part not in {"abs.", "cstr.", "nom.", "gen.", "acc.", "acc.?"}
    ]
    parts.extend([state, case])
    return Candidate(
        analysis=candidate.analysis,
        dulat=candidate.dulat,
        pos=" ".join(parts),
        gloss=candidate.gloss,
        comment=candidate.comment,
    )


def _dedupe_candidates(candidates: tuple[Candidate, ...]) -> tuple[Candidate, ...]:
    deduped: list[Candidate] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for candidate in candidates:
        key = (
            candidate.analysis,
            candidate.dulat,
            candidate.pos,
            candidate.gloss,
            candidate.comment,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return tuple(deduped)


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
