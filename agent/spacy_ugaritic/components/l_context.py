"""Rule-based spaCy component for `l`-context disambiguation."""

import re
from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.config.l_attestation_translation_cues import (
    L_CERTAINTY_TRANSLATION_CUES,
    L_INTERJECTION_TRANSLATION_CUES,
    L_NEGATION_TRANSLATION_CUES,
)
from pipeline.config.l_body_compound_prep_rules import L_BODY_COMPOUND_PREP_RULES
from pipeline.config.l_functor_vocative_refs import expected_l_homonym_for_ref
from pipeline.config.l_negation_exception_refs import is_forced_l_negation_ref
from pipeline.config.l_preposition_bigram_rules import (
    L_BAAL_ANALYSIS,
    L_BAAL_DULAT,
    L_BAAL_SURFACE,
    L_FORCE_I_BIGRAM_SURFACES,
    L_PN_FAMILY_FORCE_I_SURFACES,
    L_PN_PREP_CANONICAL_PAYLOADS,
    CanonicalSecondPayload,
)
from pipeline.dulat_attestation_translation_index import DulatAttestationTranslationIndex
from spacy_ugaritic.types import Candidate

_TRANSLATION_WORD_RE = re.compile(r"[A-Za-z']+")


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: tuple[Candidate, ...]
    after: tuple[Candidate, ...]


def _is_l_candidate(candidate: Candidate, homonym: str) -> bool:
    return candidate.analysis == f"l({homonym})" and candidate.dulat == f"l ({homonym})"


def _first_comment(token: Token) -> str:
    candidates = token._.resolved_candidates or token._.candidates
    if not candidates:
        return ""
    return candidates[0].comment


def _canonical_l(homonym: str, comment: str = "") -> Candidate:
    if homonym == "I":
        return Candidate("l(I)", "l (I)", "prep.", "to", comment=comment)
    if homonym == "II":
        return Candidate("l(II)", "l (II)", "adv.", "no", comment=comment)
    if homonym == "III":
        return Candidate("l(III)", "l (III)", "functor", "certainly", comment=comment)
    if homonym == "IV":
        return Candidate("l(IV)", "l (IV)", "interj.", "oh!", comment=comment)
    raise ValueError(homonym)


def _matches_payload(candidate: Candidate, payload: CanonicalSecondPayload) -> bool:
    return (
        candidate.analysis == payload.analysis
        and candidate.dulat == payload.dulat
        and candidate.pos == payload.pos
        and candidate.gloss == payload.gloss
    )


def _canonical_second(payload: CanonicalSecondPayload, comment: str = "") -> Candidate:
    return Candidate(payload.analysis, payload.dulat, payload.pos, payload.gloss, comment=comment)


def _canonical_kbd_compound(comment: str = "") -> Candidate:
    return Candidate("kbd(I)/", "kbd (I)", "n.", "within", comment=comment)


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
    return (_canonical_l(homonym, comment=_first_comment(token)),)


def _keep_single_payload(
    token: Token,
    payload: CanonicalSecondPayload,
) -> tuple[Candidate, ...]:
    matches = tuple(
        candidate
        for candidate in token._.resolved_candidates
        if _matches_payload(candidate, payload)
    )
    if matches:
        return (matches[0],)
    return (_canonical_second(payload, comment=_first_comment(token)),)


def _has_class(token: Token | None, label: str) -> bool:
    if token is None:
        return False
    return label in token._.coarse_classes


def _next_token(doc: Doc, index: int) -> Token | None:
    if index + 1 >= len(doc):
        return None
    return doc[index + 1]


def _l_candidate_homonym(candidate: Candidate) -> str:
    if candidate.dulat.startswith("l (") and candidate.dulat.endswith(")"):
        return candidate.dulat[3:-1]
    return ""


def _translation_words(text: str) -> frozenset[str]:
    return frozenset(match.group(0).lower() for match in _TRANSLATION_WORD_RE.finditer(text or ""))


def _translation_supports_l_homonym(translation: str, homonym: str) -> bool:
    words = _translation_words(translation)
    if homonym == "II":
        return bool(words & L_NEGATION_TRANSLATION_CUES)
    if homonym == "III":
        return bool(words & L_CERTAINTY_TRANSLATION_CUES)
    if homonym == "IV":
        return bool(words & L_INTERJECTION_TRANSLATION_CUES)
    return False


class LContextResolver:
    def __init__(self, translation_index: DulatAttestationTranslationIndex | None = None) -> None:
        self._translation_index = translation_index or DulatAttestationTranslationIndex.empty()

    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("l_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        for index, token in enumerate(doc):
            if token.text != "l":
                continue
            next_token = _next_token(doc, index)
            next_has_verb = _has_class(next_token, "VERB")
            if is_forced_l_negation_ref(token._.section_ref):
                self._replace(token, _keep_single_l(token, "II"), "forced-ii", doc)
                continue
            if self._apply_compound_rules(token, next_token, doc):
                continue
            forced = expected_l_homonym_for_ref(token._.section_ref, next_has_verb)
            if forced is not None:
                self._replace(token, _keep_single_l(token, forced), f"forced-{forced.lower()}", doc)
                continue
            translated = self._resolve_by_attestation_translation(token)
            if translated is not None:
                self._replace(
                    token,
                    _keep_single_l(token, translated),
                    f"translation-{translated.lower()}",
                    doc,
                )
                continue
            if next_has_verb:
                continue
            if any(_is_l_candidate(candidate, "I") for candidate in token._.resolved_candidates):
                self._replace(token, _keep_single_l(token, "I"), "prefer-l-i-no-verb", doc)
                continue
            filtered = tuple(
                candidate
                for candidate in token._.resolved_candidates
                if not _is_l_candidate(candidate, "II")
            )
            if filtered and len(filtered) != len(token._.resolved_candidates):
                self._replace(token, filtered, "prune-l-ii-no-verb", doc)
        return doc

    def _resolve_by_attestation_translation(self, token: Token) -> str | None:
        matched_homonyms: set[str] = set()
        for candidate in token._.resolved_candidates:
            homonym = _l_candidate_homonym(candidate)
            if homonym not in {"II", "III", "IV"}:
                continue
            translations = self._translation_index.translations_for_variant_token(
                candidate.dulat,
                token._.section_ref,
            )
            if any(
                _translation_supports_l_homonym(translation, homonym)
                for translation in translations
            ):
                matched_homonyms.add(homonym)
        if len(matched_homonyms) != 1:
            return None
        return next(iter(matched_homonyms))

    def _apply_compound_rules(self, token: Token, next_token: Token | None, doc: Doc) -> bool:
        if next_token is None:
            return False

        if next_token.text == "kbd":
            self._replace(token, _keep_single_l(token, "I"), "force-l-i-kbd", doc)
            kbd_candidates = tuple(c for c in next_token._.resolved_candidates if _is_kbd_i(c))
            kbd_comment = (
                kbd_candidates[0].comment if kbd_candidates else _first_comment(next_token)
            )
            self._replace(
                next_token,
                (_canonical_kbd_compound(comment=kbd_comment),),
                "force-kbd-compound",
                doc,
            )
            return True

        body_rule = L_BODY_COMPOUND_PREP_RULES.get(next_token.text)
        if body_rule is not None:
            self._replace(token, _keep_single_l(token, "I"), f"force-l-i-{next_token.text}", doc)
            self._replace(
                next_token,
                _keep_single_payload(
                    next_token,
                    CanonicalSecondPayload(
                        analysis=body_rule.second_analysis,
                        dulat=body_rule.second_dulat,
                        pos=body_rule.second_pos,
                        gloss=body_rule.second_gloss,
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
                    _keep_single_payload(next_token, payload),
                    f"force-pn-{next_token.text}",
                    doc,
                )
            return True

        if next_token.text == L_BAAL_SURFACE and doc._.source_name.startswith("KTU 4.") is False:
            baal_candidates = tuple(c for c in next_token._.resolved_candidates if _is_baal_ii(c))
            if baal_candidates:
                preferred_baal = next(
                    (candidate for candidate in baal_candidates if "DN" in (candidate.pos or "")),
                    baal_candidates[0],
                )
                self._replace(token, _keep_single_l(token, "I"), "force-l-i-baal", doc)
                self._replace(next_token, (preferred_baal,), "force-baal-ii", doc)
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
def make_l_context_resolver(nlp, name, dulat_db_path: str = ""):
    if dulat_db_path:
        return LContextResolver(
            translation_index=DulatAttestationTranslationIndex.from_sqlite(dulat_db_path)
        )
    return LContextResolver()
