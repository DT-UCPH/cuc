"""Generic last-resort homonym resolver from exact-citation DULAT quote translations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.dulat_attestation_translation_index import DulatAttestationTranslationIndex
from spacy_ugaritic.types import Candidate

_TRANSLATION_WORD_RE = re.compile(r"[A-Za-z']+")
_GENERIC_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "be",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "or",
        "someone",
        "something",
        "the",
        "their",
        "there",
        "these",
        "this",
        "those",
        "to",
        "with",
    }
)
_ALLOWED_SHORT_CUES = frozenset(
    {
        "as",
        "day",
        "god",
        "if",
        "like",
        "no",
        "now",
        "oh",
        "sea",
        "son",
        "sun",
        "yes",
        "when",
        "thus",
        "here",
    }
)


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: tuple[Candidate, ...]
    after: tuple[Candidate, ...]


def _translation_words(text: str) -> frozenset[str]:
    return frozenset(match.group(0).lower() for match in _TRANSLATION_WORD_RE.finditer(text or ""))


def _candidate_cues(candidate: Candidate) -> tuple[str, ...]:
    cues: list[str] = []
    for word in _translation_words(candidate.gloss):
        if word in _GENERIC_STOPWORDS:
            continue
        if len(word) >= 4 or word in _ALLOWED_SHORT_CUES:
            if word not in cues:
                cues.append(word)
    return tuple(cues)


def _append_comment(existing: str, note: str) -> str:
    current = (existing or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current} | {note}"


def _with_comment(candidate: Candidate, note: str) -> Candidate:
    return Candidate(
        analysis=candidate.analysis,
        dulat=candidate.dulat,
        pos=candidate.pos,
        gloss=candidate.gloss,
        comment=_append_comment(candidate.comment, note),
    )


class QuoteTranslationResolver:
    """Resolve ambiguous candidates from exact-citation DULAT quote translations."""

    def __init__(self, translation_index: DulatAttestationTranslationIndex | None = None) -> None:
        self._translation_index = translation_index or DulatAttestationTranslationIndex.empty()

    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("quote_translation_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        for token in doc:
            candidates = tuple(token._.resolved_candidates)
            if len(candidates) <= 1:
                continue
            section_ref = token._.section_ref
            if not section_ref:
                continue
            translations = self._translation_index.translations_for_surface_at_reference(
                token.text,
                section_ref,
            )
            if not translations:
                continue
            translation_words: set[str] = set()
            for translation in translations:
                translation_words.update(_translation_words(translation))
            if not translation_words:
                continue

            winners: list[tuple[Candidate, tuple[str, ...]]] = []
            for candidate in candidates:
                cues = tuple(cue for cue in _candidate_cues(candidate) if cue in translation_words)
                if cues:
                    winners.append((candidate, cues))
            if len(winners) != 1:
                continue

            winner, cues = winners[0]
            note = f"DULAT quote {section_ref} (cue: {cues[0]})"
            resolved = (_with_comment(winner, note),)
            self._replace(token, resolved, "translation-last-resort", doc)
        return doc

    def _replace(
        self,
        token: Token,
        candidates: tuple[Candidate, ...],
        rule: str,
        doc: Doc,
    ) -> None:
        before = token._.resolved_candidates
        if before == candidates:
            return
        token._.resolved_candidates = candidates
        doc.user_data["quote_translation_events"].append(
            ResolutionEvent(token.i, rule, before, candidates)
        )


@Language.factory("ugaritic_quote_translation_resolver")
def make_quote_translation_resolver(nlp, name, dulat_db_path: str = ""):
    if dulat_db_path:
        return QuoteTranslationResolver(
            translation_index=DulatAttestationTranslationIndex.from_sqlite(dulat_db_path)
        )
    return QuoteTranslationResolver()
