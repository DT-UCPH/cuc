"""Rule-based spaCy component for lexical-context disambiguation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.dulat_attestation_index import DulatAttestationIndex
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
_MLK_VERBAL_DULAT = "/m-l-k/"
_MLK_TITLE_DULAT = "mlk (I)"
_MLK_KINGDOM_DULAT = "mlk (II)"
_MLK_TITLE_GLOSS = "king"
_MLK_TITLE_NEXT_SURFACES = frozenset({"ab", "bn", "bnk", "ugrt", "ṣr", "šmy", "šink"})
_MLK_TITLE_PREV_SURFACES = frozenset({"l", "lpn", "pn", "tḥm"})
_ANAT_DN_DULAT = "ʕnt (I)"
_ANAT_EYE_DULAT = "ʕn (I)"
_ANAT_NOW_DULAT = "ʕnt (II)"
_ANAT_DN_PREV_SURFACES = frozenset(
    {
        "aṯrt",
        "ap",
        "bht",
        "bˤl",
        "btlt",
        "hln",
        "hlm",
        "kbd",
        "l",
        "lb",
        "lt",
        "pˤn",
        "pl",
        "rḥm",
        "ršp",
        "š",
        "tḥdy",
        "ugrt",
        "ˤt",
        "ḥmt",
    }
)


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


def _is_baal_nominal(candidate: Candidate) -> bool:
    return candidate.analysis.strip() == "bˤl(II)/" and candidate.dulat.strip() == "bʕl (II)"


def _is_baal_verbal(candidate: Candidate) -> bool:
    return candidate.dulat.strip() == _BAAL_VERBAL_DULAT


def _is_bt_house(candidate: Candidate) -> bool:
    return candidate.analysis.strip() == "bt(II)/" and candidate.dulat.strip() == "bt (II)"


def _is_bt_daughter(candidate: Candidate) -> bool:
    return candidate.analysis.strip() == "b(t(I)/t" and candidate.dulat.strip() == "bt (I)"


def _is_mlk_verbal(candidate: Candidate) -> bool:
    return candidate.dulat.strip() == _MLK_VERBAL_DULAT


def _is_mlk_kingdom(candidate: Candidate) -> bool:
    return (
        candidate.analysis.strip() == "mlk(II)/" and candidate.dulat.strip() == _MLK_KINGDOM_DULAT
    )


def _is_mlk_title(candidate: Candidate) -> bool:
    return candidate.analysis.strip() == "mlk(I)/" and candidate.dulat.strip() == _MLK_TITLE_DULAT


def _is_anat_divine(candidate: Candidate) -> bool:
    return candidate.analysis.strip() == "ˤn(t(I)/t" and candidate.dulat.strip() == _ANAT_DN_DULAT


def _is_anat_eye(candidate: Candidate) -> bool:
    return candidate.analysis.strip() == "ˤn(I)/t=" and candidate.dulat.strip() == _ANAT_EYE_DULAT


def _is_anat_now(candidate: Candidate) -> bool:
    return candidate.analysis.strip() == "ˤnt(II)" and candidate.dulat.strip() == _ANAT_NOW_DULAT


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
    def __init__(self, *, rule_groups: Iterable[str] = ("baal", "anat", "ydk", "mlk")) -> None:
        self._rule_groups = frozenset(rule_groups)

    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("lexical_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        if "baal" in self._rule_groups:
            self._apply_baal_rules(doc)
        if "anat" in self._rule_groups:
            self._apply_anat_rules(doc)
        if "mlk" in self._rule_groups:
            self._apply_mlk_rules(doc)
        if "ydk" in self._rule_groups:
            self._apply_ydk_rules(doc)
        return doc

    def _apply_baal_rules(self, doc: Doc) -> None:
        allow_labourer = _is_ktu4(doc)
        attestation_index = doc.user_data.get("attestation_index")
        if not isinstance(attestation_index, DulatAttestationIndex):
            attestation_index = DulatAttestationIndex.empty()
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
                    normalized = _prune_unattested_baal_verbal(
                        normalized,
                        section_ref=token._.section_ref,
                        attestation_index=attestation_index,
                    )
                self._maybe_replace(token, normalized, "baal-lexical")
                continue
            if token._.surface == "bt":
                normalized = _resolve_bt_baal_phrase(
                    doc,
                    index,
                    candidates,
                    attestation_index=attestation_index,
                )
                self._maybe_replace(token, normalized, "bt-baal-context")
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

    def _apply_anat_rules(self, doc: Doc) -> None:
        attestation_index = doc.user_data.get("attestation_index")
        if not isinstance(attestation_index, DulatAttestationIndex):
            attestation_index = DulatAttestationIndex.empty()
        for index, token in enumerate(doc):
            if token._.surface != "ˤnt":
                continue
            candidates = tuple(token._.resolved_candidates)
            normalized = _resolve_anat_context(
                doc,
                index,
                candidates,
                attestation_index=attestation_index,
            )
            self._maybe_replace(token, normalized, "anat-divine-name-context")

    def _apply_mlk_rules(self, doc: Doc) -> None:
        attestation_index = doc.user_data.get("attestation_index")
        if not isinstance(attestation_index, DulatAttestationIndex):
            attestation_index = DulatAttestationIndex.empty()
        for index, token in enumerate(doc):
            if token._.surface != "mlk":
                continue
            candidates = tuple(token._.resolved_candidates)
            normalized = _resolve_mlk_context(
                doc,
                index,
                candidates,
                attestation_index=attestation_index,
            )
            self._maybe_replace(token, normalized, "mlk-title-context")

    def _maybe_replace(self, token: Token, candidates: tuple[Candidate, ...], rule: str) -> None:
        before = tuple(token._.resolved_candidates)
        if candidates == before:
            return
        token._.resolved_candidates = candidates
        token.doc.user_data["lexical_context_events"].append(
            ResolutionEvent(token.i, rule, before, candidates)
        )


@Language.factory("ugaritic_lexical_context_resolver")
def make_lexical_context_resolver(nlp, name, rule_groups=("baal", "anat", "ydk", "mlk")):
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


def _is_anat_divine_name_context(doc: Doc, index: int) -> bool:
    if index < 0 or index >= len(doc) or doc[index]._.surface != "ˤnt":
        return False
    if index == 0:
        return False
    return doc[index - 1]._.surface in _ANAT_DN_PREV_SURFACES


def _prune_unattested_baal_verbal(
    candidates: tuple[Candidate, ...],
    *,
    section_ref: str,
    attestation_index: DulatAttestationIndex,
) -> tuple[Candidate, ...]:
    """Drop `/b-ʕ-l/` when `bʕl (II)` is present and the verb lacks direct attestation."""
    has_nominal = any(_is_baal_nominal(candidate) for candidate in candidates)
    has_verbal = any(_is_baal_verbal(candidate) for candidate in candidates)
    if not has_nominal or not has_verbal:
        return candidates
    if attestation_index.has_reference_for_variant_token(_BAAL_VERBAL_DULAT, section_ref):
        return candidates
    filtered = tuple(candidate for candidate in candidates if not _is_baal_verbal(candidate))
    return filtered or candidates


def _is_bt_baal_phrase(doc: Doc, index: int) -> bool:
    if index < 0 or index >= len(doc) or doc[index]._.surface != "bt":
        return False
    if index + 1 >= len(doc):
        return False
    next_surface = doc[index + 1]._.surface
    if next_surface == "lbˤl":
        return True
    if next_surface != "l" or index + 2 >= len(doc):
        return False
    return doc[index + 2]._.surface == "bˤl"


def _resolve_bt_baal_phrase(
    doc: Doc,
    index: int,
    candidates: tuple[Candidate, ...],
    *,
    attestation_index: DulatAttestationIndex,
) -> tuple[Candidate, ...]:
    has_house = any(_is_bt_house(candidate) for candidate in candidates)
    has_daughter = any(_is_bt_daughter(candidate) for candidate in candidates)
    if not has_house or not has_daughter:
        return candidates
    section_ref = doc[index]._.section_ref
    if _is_bt_baal_phrase(doc, index) or attestation_index.has_reference_for_variant_token(
        "bt (II)",
        section_ref,
    ):
        filtered = tuple(candidate for candidate in candidates if _is_bt_house(candidate))
        return filtered or candidates
    filtered = tuple(candidate for candidate in candidates if not _is_bt_house(candidate))
    return filtered or candidates


def _resolve_anat_context(
    doc: Doc,
    index: int,
    candidates: tuple[Candidate, ...],
    *,
    attestation_index: DulatAttestationIndex,
) -> tuple[Candidate, ...]:
    has_divine = any(_is_anat_divine(candidate) for candidate in candidates)
    has_eye = any(_is_anat_eye(candidate) for candidate in candidates)
    has_now = any(_is_anat_now(candidate) for candidate in candidates)
    if not has_divine or (not has_eye and not has_now):
        return candidates

    section_ref = doc[index]._.section_ref
    if attestation_index.has_reference_for_variant_token(_ANAT_EYE_DULAT, section_ref):
        filtered = tuple(candidate for candidate in candidates if _is_anat_eye(candidate))
        return filtered or candidates
    if attestation_index.has_reference_for_variant_token(_ANAT_NOW_DULAT, section_ref):
        filtered = tuple(candidate for candidate in candidates if _is_anat_now(candidate))
        return filtered or candidates
    if not _is_anat_divine_name_context(doc, index):
        return candidates

    filtered = tuple(candidate for candidate in candidates if _is_anat_divine(candidate))
    return filtered or candidates


def _canonical_mlk_title(comment: str, nominal_candidate: Candidate) -> Candidate:
    return Candidate(
        "mlk(I)/",
        _MLK_TITLE_DULAT,
        nominal_candidate.pos,
        _MLK_TITLE_GLOSS,
        comment=comment,
    )


def _is_nominal_genitive_target(token: Token) -> bool:
    for candidate in token._.resolved_candidates:
        pos = candidate.pos
        if "TN" in pos or "DN" in pos or "PN" in pos or "n." in pos or "adj." in pos:
            return True
    return False


def _is_toponym(token: Token) -> bool:
    return any("TN" in candidate.pos for candidate in token._.resolved_candidates)


def _is_mlk_title_context(doc: Doc, index: int) -> bool:
    token = doc[index]
    previous = doc[index - 1] if index > 0 else None
    next_token = doc[index + 1] if index + 1 < len(doc) else None
    if next_token is not None:
        if _is_toponym(next_token):
            return True
        if any("cstr." in candidate.pos for candidate in token._.resolved_candidates):
            if _is_nominal_genitive_target(next_token):
                return True
        if next_token._.surface in _MLK_TITLE_NEXT_SURFACES:
            return True
        if previous is not None and previous._.surface in _MLK_TITLE_PREV_SURFACES:
            if _is_nominal_genitive_target(next_token):
                return True
    if previous is not None:
        if any("PN" in candidate.pos for candidate in previous._.resolved_candidates):
            return True
        if previous._.surface == "il":
            return True
    return False


def _resolve_mlk_context(
    doc: Doc,
    index: int,
    candidates: tuple[Candidate, ...],
    *,
    attestation_index: DulatAttestationIndex,
) -> tuple[Candidate, ...]:
    has_title = any(_is_mlk_title(candidate) for candidate in candidates)
    has_kingdom = any(_is_mlk_kingdom(candidate) for candidate in candidates)
    has_verbal = any(_is_mlk_verbal(candidate) for candidate in candidates)
    if has_title or (not has_kingdom and not has_verbal):
        return candidates
    section_ref = doc[index]._.section_ref
    if attestation_index.has_reference_for_variant_token(_MLK_VERBAL_DULAT, section_ref):
        return candidates
    if not (
        attestation_index.has_reference_for_variant_token(_MLK_TITLE_DULAT, section_ref)
        or _is_mlk_title_context(doc, index)
    ):
        return candidates

    nominal_candidate = next(
        (candidate for candidate in candidates if _is_mlk_kingdom(candidate)),
        None,
    )
    if nominal_candidate is None:
        return candidates
    comment = next((candidate.comment for candidate in candidates if candidate.comment), "")
    replacement = _canonical_mlk_title(comment, nominal_candidate)
    preserved = tuple(
        candidate
        for candidate in candidates
        if not _is_mlk_verbal(candidate) and not _is_mlk_kingdom(candidate)
    )
    return (*preserved, replacement) if preserved else (replacement,)
