"""Rule-based spaCy component for `l`-context disambiguation."""

from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.config.l_body_compound_prep_rules import L_BODY_COMPOUND_PREP_RULES
from pipeline.config.l_functor_vocative_refs import expected_l_homonym_for_ref
from pipeline.config.l_preposition_bigram_rules import (
    L_BAAL_ANALYSIS,
    L_BAAL_DULAT,
    L_BAAL_SURFACE,
    L_FORCE_I_BIGRAM_SURFACES,
    L_PN_FAMILY_FORCE_I_SURFACES,
    L_PN_PREP_CANONICAL_PAYLOADS,
    CanonicalSecondPayload,
)
from spacy_ugaritic_types import Candidate


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: tuple[Candidate, ...]
    after: tuple[Candidate, ...]


def _is_l_candidate(candidate: Candidate, homonym: str) -> bool:
    return candidate.analysis == f"l({homonym})" and candidate.dulat == f"l ({homonym})"


def _canonical_l(homonym: str, source: Token) -> Candidate:
    if homonym == "I":
        return Candidate("l(I)", "l (I)", "prep.", "to")
    if homonym == "II":
        return Candidate("l(II)", "l (II)", "adv.", "no")
    if homonym == "III":
        return Candidate("l(III)", "l (III)", "functor", "certainly")
    if homonym == "IV":
        return Candidate("l(IV)", "l (IV)", "interj.", "oh!")
    raise ValueError(homonym)


def _matches_payload(candidate: Candidate, payload: CanonicalSecondPayload) -> bool:
    return (
        candidate.analysis == payload.analysis
        and candidate.dulat == payload.dulat
        and candidate.pos == payload.pos
        and candidate.gloss == payload.gloss
    )


def _canonical_second(payload: CanonicalSecondPayload, source: Token) -> Candidate:
    return Candidate(payload.analysis, payload.dulat, payload.pos, payload.gloss)


def _canonical_kbd_compound() -> Candidate:
    return Candidate("kbd(I)/", "kbd (I)", "n.", "within")


def _is_kbd_i(candidate: Candidate) -> bool:
    return candidate.analysis == "kbd(I)/" and candidate.dulat == "kbd (I)"


def _is_baal_ii(candidate: Candidate) -> bool:
    return candidate.analysis == L_BAAL_ANALYSIS and candidate.dulat == L_BAAL_DULAT


def _keep_single_l(token: Token, homonym: str) -> tuple[Candidate, ...]:
    matches = tuple(
        candidate
        for candidate in token._.resolved_candidates
        if _is_l_candidate(candidate, homonym)
    )
    if matches:
        return (matches[0],)
    return (_canonical_l(homonym, token),)


def _has_class(token: Token | None, label: str) -> bool:
    if token is None:
        return False
    return label in token._.coarse_classes


def _next_token(doc: Doc, index: int) -> Token | None:
    if index + 1 >= len(doc):
        return None
    return doc[index + 1]


class LContextResolver:
    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("l_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        for index, token in enumerate(doc):
            if token.text != "l":
                continue
            next_token = _next_token(doc, index)
            next_has_verb = _has_class(next_token, "VERB")
            forced = expected_l_homonym_for_ref(token._.section_ref, next_has_verb)
            if forced is not None:
                self._replace(token, _keep_single_l(token, forced), f"forced-{forced.lower()}", doc)
                continue
            if self._apply_compound_rules(token, next_token, doc):
                continue
            if next_has_verb:
                continue
            filtered = tuple(
                candidate
                for candidate in token._.resolved_candidates
                if not _is_l_candidate(candidate, "II")
            )
            if filtered and len(filtered) != len(token._.resolved_candidates):
                self._replace(token, filtered, "prune-l-ii-no-verb", doc)
        return doc

    def _apply_compound_rules(self, token: Token, next_token: Token | None, doc: Doc) -> bool:
        if next_token is None:
            return False

        if next_token.text == "kbd" and any(_is_kbd_i(c) for c in next_token._.resolved_candidates):
            self._replace(token, _keep_single_l(token, "I"), "force-l-i-kbd", doc)
            self._replace(next_token, (_canonical_kbd_compound(),), "force-kbd-compound", doc)
            return True

        body_rule = L_BODY_COMPOUND_PREP_RULES.get(next_token.text)
        if body_rule is not None and any(
            c.analysis == body_rule.second_analysis and c.dulat == body_rule.second_dulat
            for c in next_token._.resolved_candidates
        ):
            self._replace(token, _keep_single_l(token, "I"), f"force-l-i-{next_token.text}", doc)
            self._replace(
                next_token,
                (
                    _canonical_second(
                        CanonicalSecondPayload(
                            analysis=body_rule.second_analysis,
                            dulat=body_rule.second_dulat,
                            pos=body_rule.second_pos,
                            gloss=body_rule.second_gloss,
                        ),
                        next_token,
                    ),
                ),
                f"force-body-{next_token.text}",
                doc,
            )
            return True

        if (
            next_token.text in L_FORCE_I_BIGRAM_SURFACES
            or next_token.text in L_PN_FAMILY_FORCE_I_SURFACES
        ):
            self._replace(token, _keep_single_l(token, "I"), f"force-l-i-{next_token.text}", doc)
            payload = L_PN_PREP_CANONICAL_PAYLOADS.get(next_token.text)
            if payload is not None:
                self._replace(
                    next_token,
                    (_canonical_second(payload, next_token),),
                    f"force-pn-{next_token.text}",
                    doc,
                )
            return True

        if next_token.text == L_BAAL_SURFACE and doc._.source_name.startswith("KTU 4.") is False:
            baal_candidates = tuple(c for c in next_token._.resolved_candidates if _is_baal_ii(c))
            if baal_candidates:
                self._replace(token, _keep_single_l(token, "I"), "force-l-i-baal", doc)
                self._replace(next_token, (baal_candidates[0],), "force-baal-ii", doc)
                return True
        return False

    def _replace(
        self, token: Token, candidates: tuple[Candidate, ...], rule: str, doc: Doc
    ) -> None:
        before = token._.resolved_candidates
        if before == candidates:
            return
        token._.resolved_candidates = candidates
        doc.user_data["l_context_events"].append(ResolutionEvent(token.i, rule, before, candidates))


@Language.factory("ugaritic_l_context_resolver")
def make_l_context_resolver(nlp, name):
    return LContextResolver()
