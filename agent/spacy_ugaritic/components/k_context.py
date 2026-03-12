"""Rule-based spaCy component for `k`-context disambiguation."""

import re
from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.config.k_attestation_translation_cues import (
    K_ADVERB_TRANSLATION_CUES,
    K_EMPHATIC_TRANSLATION_CUES,
    K_PREPOSITION_TRANSLATION_CUES,
    K_SUBORDINATING_TRANSLATION_CUES,
)
from pipeline.config.k_functor_bigram_surfaces import K_FUNCTOR_VERB_BIGRAM_SURFACES
from pipeline.dulat_attestation_translation_index import DulatAttestationTranslationIndex
from spacy_ugaritic.types import Candidate

_TRANSLATION_WORD_RE = re.compile(r"[A-Za-z']+")


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: tuple[Candidate, ...]
    after: tuple[Candidate, ...]


def _is_k_iii_candidate(candidate: Candidate) -> bool:
    return candidate.analysis == "k(III)" and candidate.dulat == "k (III)"


def _is_k_i_candidate(candidate: Candidate) -> bool:
    return candidate.analysis == "k(I)" and candidate.dulat == "k (I)"


def _is_k_ii_candidate(candidate: Candidate) -> bool:
    return candidate.analysis == "k(II)" and candidate.dulat == "k (II)"


def _is_k_iv_candidate(candidate: Candidate) -> bool:
    return candidate.analysis == "k(IV)" and candidate.dulat == "k (IV)"


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


def _canonical_k_i(comment: str = "") -> Candidate:
    return Candidate("k(I)", "k (I)", "prep.", "like", comment=comment)


def _canonical_k_ii(comment: str = "") -> Candidate:
    return Candidate("k(II)", "k (II)", "emph. functor", "yes", comment=comment)


def _canonical_k_iv(comment: str = "") -> Candidate:
    return Candidate("k(IV)", "k (IV)", "adv.", "thus", comment=comment)


def _keep_single_k_iii(token: Token) -> tuple[Candidate, ...]:
    matches = tuple(
        candidate for candidate in token._.resolved_candidates if _is_k_iii_candidate(candidate)
    )
    if matches:
        return (matches[0],)
    return (_canonical_k_iii(comment=_first_comment(token)),)


def _keep_single_k(token: Token, homonym: str) -> tuple[Candidate, ...]:
    predicates = {
        "I": _is_k_i_candidate,
        "II": _is_k_ii_candidate,
        "III": _is_k_iii_candidate,
        "IV": _is_k_iv_candidate,
    }
    canonicals = {
        "I": _canonical_k_i,
        "II": _canonical_k_ii,
        "III": _canonical_k_iii,
        "IV": _canonical_k_iv,
    }
    predicate = predicates[homonym]
    matches = tuple(candidate for candidate in token._.resolved_candidates if predicate(candidate))
    if matches:
        return (matches[0],)
    return (canonicals[homonym](comment=_first_comment(token)),)


def _has_class(token: Token | None, label: str) -> bool:
    if token is None:
        return False
    return label in token._.coarse_classes


def _next_token(doc: Doc, index: int) -> Token | None:
    if index + 1 >= len(doc):
        return None
    return doc[index + 1]


def _translation_words(text: str) -> frozenset[str]:
    return frozenset(match.group(0).lower() for match in _TRANSLATION_WORD_RE.finditer(text or ""))


def _translation_supports_k_homonym(translation: str, homonym: str) -> bool:
    words = _translation_words(translation)
    if homonym == "I":
        return bool(words & K_PREPOSITION_TRANSLATION_CUES)
    if homonym == "II":
        return bool(words & K_EMPHATIC_TRANSLATION_CUES)
    if homonym == "III":
        return bool(words & K_SUBORDINATING_TRANSLATION_CUES)
    if homonym == "IV":
        return bool(words & K_ADVERB_TRANSLATION_CUES)
    return False


def _cue_for_k_translation(translation: str, homonym: str) -> str:
    words = _translation_words(translation)
    if homonym == "I":
        cues = sorted(words & K_PREPOSITION_TRANSLATION_CUES)
    elif homonym == "II":
        cues = sorted(words & K_EMPHATIC_TRANSLATION_CUES)
    elif homonym == "III":
        cues = sorted(words & K_SUBORDINATING_TRANSLATION_CUES)
    elif homonym == "IV":
        cues = sorted(words & K_ADVERB_TRANSLATION_CUES)
    else:
        cues = []
    return cues[0] if cues else ""


def _append_comment(existing: str, note: str) -> str:
    current = (existing or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current} | {note}"


def _annotate_candidates(
    candidates: tuple[Candidate, ...],
    *,
    article: str,
    cue: str,
) -> tuple[Candidate, ...]:
    note = f"DULAT quote in {article} (cue: {cue})" if article else f"DULAT quote (cue: {cue})"
    out: list[Candidate] = []
    for candidate in candidates:
        out.append(
            Candidate(
                candidate.analysis,
                candidate.dulat,
                candidate.pos,
                candidate.gloss,
                _append_comment(candidate.comment, note),
            )
        )
    return tuple(out)


class KContextResolver:
    def __init__(self, translation_index: DulatAttestationTranslationIndex | None = None) -> None:
        self._translation_index = translation_index or DulatAttestationTranslationIndex.empty()

    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("k_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        for index, token in enumerate(doc):
            if token.text != "k":
                continue
            next_token = _next_token(doc, index)
            if (
                next_token is not None
                and next_token.text in K_FUNCTOR_VERB_BIGRAM_SURFACES
                and _has_class(next_token, "VERB")
            ):
                self._replace(
                    token,
                    _keep_single_k_iii(token),
                    f"force-k-iii-{next_token.text}",
                    doc,
                )
                continue

            translated = self._resolve_by_citation_translation(token)
            if translated is None:
                continue
            self._replace(
                token,
                _annotate_candidates(
                    _keep_single_k(token, translated[0]),
                    article=translated[2],
                    cue=translated[1],
                ),
                f"translation-{translated[0].lower()}",
                doc,
            )
        return doc

    def _resolve_by_citation_translation(self, token: Token) -> tuple[str, str, str] | None:
        evidence_items = self._translation_index.translation_evidence_for_surface_at_reference(
            token.text,
            token._.section_ref,
        )
        if not evidence_items:
            return None
        matched_homonyms: dict[str, tuple[str, str]] = {}
        for homonym in ("I", "II", "III", "IV"):
            matched = False
            cue = ""
            article = ""
            for evidence in evidence_items:
                translation = evidence.translation
                if not _translation_supports_k_homonym(translation, homonym):
                    continue
                cue = _cue_for_k_translation(translation, homonym) or homonym.lower()
                article = evidence.article
                matched = True
                break
            if not matched:
                continue
            if homonym == "I" and any(
                _is_k_i_candidate(c) for c in token._.resolved_candidates
            ):
                matched_homonyms[homonym] = (cue, article)
            if homonym == "II" and any(
                _is_k_ii_candidate(c) for c in token._.resolved_candidates
            ):
                matched_homonyms[homonym] = (cue, article)
            if homonym == "III" and any(
                _is_k_iii_candidate(c) for c in token._.resolved_candidates
            ):
                matched_homonyms[homonym] = (cue, article)
            if homonym == "IV" and any(
                _is_k_iv_candidate(c) for c in token._.resolved_candidates
            ):
                matched_homonyms[homonym] = (cue, article)
        if len(matched_homonyms) != 1:
            return None
        homonym = next(iter(matched_homonyms))
        cue, article = matched_homonyms[homonym]
        return homonym, cue, article

    def _replace(
        self, token: Token, candidates: tuple[Candidate, ...], rule: str, doc: Doc
    ) -> None:
        before = token._.resolved_candidates
        if before == candidates:
            return
        token._.resolved_candidates = candidates
        doc.user_data["k_context_events"].append(ResolutionEvent(token.i, rule, before, candidates))


@Language.factory("ugaritic_k_context_resolver")
def make_k_context_resolver(nlp, name, dulat_db_path: str = ""):
    if dulat_db_path:
        return KContextResolver(
            translation_index=DulatAttestationTranslationIndex.from_sqlite(dulat_db_path)
        )
    return KContextResolver()
