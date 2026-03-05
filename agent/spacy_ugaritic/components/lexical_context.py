"""Rule-based spaCy component for lexical-context disambiguation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from spacy.language import Language
from spacy.tokens import Doc, Token

from spacy_ugaritic.types import Candidate

_BAAL_VERBAL_DULAT = "/b-ʕ-l/"
_TARGET_ANALYSES = {
    "bˤl(II)/;bˤl(I)/;bˤl[",
    "bˤl(II)/;bˤl(I)/;bˤl[/",
}
_TARGET_DULAT = "bʕl (II);bʕl (I);/b-ʕ-l/"
_TARGET_POS = "n. m./DN;n. m.;vb"
_TARGET_GLOSS = "Baʿlu;labourer;to make"
_REPLACEMENT_ANALYSIS = "bˤl(II)/;bˤl[/"
_REPLACEMENT_DULAT = "bʕl (II);/b-ʕ-l/"
_REPLACEMENT_POS = "n. m./DN;vb"
_REPLACEMENT_GLOSS = "Baʿlu;to make"
_ALIYN_GLOSS = "the very / most powerful"
_BULL_GLOSS = "bull"
_EL_GLOSS = "ʾilu/ilu/el"


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: tuple[Candidate, ...]
    after: tuple[Candidate, ...]


def _is_ktu4(doc: Doc) -> bool:
    return (doc._.source_name or "").startswith("KTU 4.")


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def _is_baal_labourer(candidate: Candidate) -> bool:
    return (
        candidate.analysis.strip() == "bˤl(I)/"
        and candidate.dulat.strip() == "bʕl (I)"
        and "n. m." in candidate.pos
        and candidate.gloss.strip().lower() == "labourer"
    )


def _normalize_baal_verbal(candidate: Candidate) -> Candidate:
    if candidate.dulat.strip() != _BAAL_VERBAL_DULAT:
        return candidate
    analysis = candidate.analysis.strip()
    if analysis.endswith("[") and "/" not in analysis:
        return Candidate(
            analysis=f"{analysis}/",
            dulat=candidate.dulat,
            pos=candidate.pos,
            gloss=candidate.gloss,
            comment=candidate.comment,
        )
    return candidate


def _normalize_packed_baal_verbal(candidate: Candidate) -> Candidate:
    analysis_variants = _split_semicolon(candidate.analysis)
    dulat_variants = _split_semicolon(candidate.dulat)
    if not analysis_variants or not dulat_variants or len(analysis_variants) != len(dulat_variants):
        return candidate
    normalized = []
    changed = False
    for analysis_variant, dulat_variant in zip(analysis_variants, dulat_variants, strict=True):
        updated = _normalize_baal_verbal(
            Candidate(analysis_variant, dulat_variant, "", "", candidate.comment)
        ).analysis
        if updated != analysis_variant:
            changed = True
        normalized.append(updated)
    if not changed:
        return candidate
    return Candidate(
        analysis=";".join(normalized),
        dulat=candidate.dulat,
        pos=candidate.pos,
        gloss=candidate.gloss,
        comment=candidate.comment,
    )


def _canonical_baal_plural(comment: str = "") -> Candidate:
    return Candidate("bˤl(II)/m", "bʕl (II)", "n. m.", "lord", comment=comment)


def _looks_like_mixed_baal_plural(candidates: tuple[Candidate, ...]) -> bool:
    analyses = {candidate.analysis.strip() for candidate in candidates}
    dulat = {candidate.dulat.strip() for candidate in candidates}
    glosses = {candidate.gloss.strip().lower() for candidate in candidates}
    has_ii = bool({"bˤl(II)/", "bˤlm(II)/", "bˤl(II)/m"} & analyses)
    has_i_plural = "bˤl(I)/m" in analyses
    return (
        has_ii
        and has_i_plural
        and {"bʕl (II)", "bʕl (I)"}.issubset(dulat)
        and "labourer" in glosses
    )


def _looks_like_packed_baal_plural(candidate: Candidate) -> bool:
    analyses = set(_split_semicolon(candidate.analysis))
    dulat = set(_split_semicolon(candidate.dulat))
    glosses = {gloss.lower() for gloss in _split_semicolon(candidate.gloss)}
    has_ii = bool({"bˤl(II)/", "bˤlm(II)/", "bˤl(II)/m"} & analyses)
    has_i_plural = "bˤl(I)/m" in analyses
    return (
        has_ii
        and has_i_plural
        and {"bʕl (II)", "bʕl (I)"}.issubset(dulat)
        and "labourer" in glosses
    )


def _canonical_ydk(comment: str = "") -> Candidate:
    return Candidate("yd(II)/+k=", "yd (II)", "n. m. cstr. nom.", "love", comment=comment)


def _canonical_aliyn_baal(comment: str = "") -> Candidate:
    return Candidate(
        "bˤl(II)/",
        "bʕl (II)",
        "DN m. sg. abs. nom.",
        "Baʿlu/Baal",
        comment=comment,
    )


def _canonical_thr_bull(comment: str = "") -> Candidate:
    return Candidate("ṯr(I)/", "ṯr (I)", "n. m. sg. abs. nom.", "bull", comment=comment)


def _canonical_il_el(comment: str = "") -> Candidate:
    return Candidate(
        "il(I)/",
        "ỉl (I)",
        "DN m. sg. abs. nom.",
        "ʾIlu/Ilu/El",
        comment=comment,
    )


def _packed_baal_labourer_row(candidate: Candidate) -> bool:
    return (
        ";".join(_split_semicolon(candidate.analysis)) in _TARGET_ANALYSES
        and ";".join(_split_semicolon(candidate.dulat)) == _TARGET_DULAT
        and ";".join(_split_semicolon(candidate.pos)) == _TARGET_POS
        and ";".join(_split_semicolon(candidate.gloss)) == _TARGET_GLOSS
    )


class LexicalContextResolver:
    def __init__(self, *, rule_groups: Iterable[str] = ("baal", "ydk")) -> None:
        self._rule_groups = frozenset(rule_groups)

    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("lexical_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        if "baal" in self._rule_groups:
            self._apply_baal_rules(doc)
        if "ydk" in self._rule_groups:
            self._apply_ydk_rules(doc)
        return doc

    def _apply_baal_rules(self, doc: Doc) -> None:
        allow_labourer = _is_ktu4(doc)
        for index, token in enumerate(doc):
            candidates = tuple(token._.resolved_candidates)
            if token._.surface == "ṯr" and _is_thr_il_context(doc, index):
                comment = next(
                    (candidate.comment for candidate in candidates if candidate.comment),
                    "",
                )
                self._maybe_replace(token, (_canonical_thr_bull(comment),), "thr-il-bull")
                continue
            if token._.surface == "il" and _is_el_in_thr_il_context(doc, index):
                comment = next(
                    (candidate.comment for candidate in candidates if candidate.comment),
                    "",
                )
                self._maybe_replace(token, (_canonical_il_el(comment),), "thr-il-el")
                continue
            if token._.surface == "bˤl":
                if _is_aliyn_baal_context(doc, index):
                    comment = next(
                        (candidate.comment for candidate in candidates if candidate.comment),
                        "",
                    )
                    self._maybe_replace(token, (_canonical_aliyn_baal(comment),), "aliyn-baal-dn")
                    continue
                if len(candidates) == 1:
                    candidate = _normalize_packed_baal_verbal(candidates[0])
                    if not allow_labourer and _packed_baal_labourer_row(candidate):
                        replacement = (
                            Candidate(
                                _REPLACEMENT_ANALYSIS,
                                _REPLACEMENT_DULAT,
                                _REPLACEMENT_POS,
                                _REPLACEMENT_GLOSS,
                                candidate.comment,
                            ),
                        )
                        self._maybe_replace(token, replacement, "baal-labourer-packed")
                        continue
                    self._maybe_replace(token, (candidate,), "baal-verbal-packed")
                    continue
                normalized = tuple(_normalize_baal_verbal(candidate) for candidate in candidates)
                if not allow_labourer:
                    normalized = tuple(
                        candidate for candidate in normalized if not _is_baal_labourer(candidate)
                    )
                self._maybe_replace(token, normalized, "baal-lexical")
                continue
            if token._.surface != "bˤlm":
                continue
            if len(candidates) == 1:
                candidate = _normalize_packed_baal_verbal(candidates[0])
                if _looks_like_packed_baal_plural(candidate):
                    candidate = _canonical_baal_plural(candidate.comment)
                self._maybe_replace(token, (candidate,), "baal-plural-packed")
                continue
            normalized = tuple(_normalize_baal_verbal(candidate) for candidate in candidates)
            if _looks_like_mixed_baal_plural(normalized):
                comment = next(
                    (candidate.comment for candidate in normalized if candidate.comment), ""
                )
                normalized = (_canonical_baal_plural(comment),)
            self._maybe_replace(token, normalized, "baal-plural")

    def _apply_ydk_rules(self, doc: Doc) -> None:
        for index, token in enumerate(doc[:-1]):
            if token._.surface != "ydk" or doc[index + 1]._.surface != "ṣġr":
                continue
            candidates = tuple(token._.resolved_candidates)
            if not candidates:
                continue
            comment = next((candidate.comment for candidate in candidates if candidate.comment), "")
            self._maybe_replace(token, (_canonical_ydk(comment),), "ydk-love-before-ṣġr")

    def _maybe_replace(self, token: Token, candidates: tuple[Candidate, ...], rule: str) -> None:
        before = tuple(token._.resolved_candidates)
        if candidates == before:
            return
        token._.resolved_candidates = candidates
        token.doc.user_data["lexical_context_events"].append(
            ResolutionEvent(token.i, rule, before, candidates)
        )


@Language.factory("ugaritic_lexical_context_resolver")
def make_lexical_context_resolver(nlp, name, rule_groups=("baal", "ydk")):
    return LexicalContextResolver(rule_groups=rule_groups)


def _is_aliyn_baal_context(doc: Doc, index: int) -> bool:
    if index <= 0 or doc[index]._.surface != "bˤl":
        return False
    previous = doc[index - 1]
    if previous._.surface != "aliyn":
        return False
    return any(
        candidate.analysis.strip() == "aliyn/"
        and candidate.dulat.strip() == "ảlỉyn"
        and "adj." in candidate.pos
        and (candidate.gloss or "").strip().lower() == _ALIYN_GLOSS
        for candidate in previous._.resolved_candidates
    )


def _is_thr_il_context(doc: Doc, index: int) -> bool:
    if index < 0 or index + 1 >= len(doc) or doc[index]._.surface != "ṯr":
        return False
    next_token = doc[index + 1]
    if next_token._.surface != "il":
        return False
    return any(
        candidate.analysis.strip() == "ṯr(I)/"
        and candidate.dulat.strip() == "ṯr (I)"
        and candidate.gloss.strip().lower() == _BULL_GLOSS
        for candidate in doc[index]._.resolved_candidates
    ) and any(
        candidate.analysis.strip() == "il(I)/"
        and candidate.dulat.strip() == "ỉl (I)"
        and candidate.gloss.strip().lower() == _EL_GLOSS
        for candidate in next_token._.resolved_candidates
    )


def _is_el_in_thr_il_context(doc: Doc, index: int) -> bool:
    if index <= 0 or doc[index]._.surface != "il":
        return False
    return _is_thr_il_context(doc, index - 1)
