"""Rule-based spaCy component for formula bigram/trigram normalization."""

from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.config.formula_bigram_rules import FORMULA_BIGRAM_RULES, FormulaBigramRule
from pipeline.config.formula_trigram_rules import FORMULA_TRIGRAM_RULES, FormulaTrigramRule
from spacy_ugaritic.types import Candidate


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: Candidate
    after: Candidate


def _split_variants(value: str) -> list[str]:
    return [variant.strip() for variant in (value or "").split(";") if variant.strip()]


def _target_supported(candidate: Candidate, target) -> bool:
    return target.dulat in set(_split_variants(candidate.dulat))


def _has_variants(candidate: Candidate) -> bool:
    return any(
        ";" in value
        for value in (candidate.analysis, candidate.dulat, candidate.pos, candidate.gloss)
    )


def _apply_target(candidate: Candidate, target, *, require_variants: bool) -> Candidate:
    if not _target_supported(candidate, target):
        return candidate
    if (
        candidate.analysis == target.analysis
        and candidate.dulat == target.dulat
        and candidate.pos == target.pos
        and candidate.gloss == target.gloss
    ):
        return candidate
    if require_variants and not _has_variants(candidate):
        return candidate
    return Candidate(
        analysis=target.analysis,
        dulat=target.dulat,
        pos=target.pos,
        gloss=target.gloss,
        comment=candidate.comment,
    )


def _build_target(candidate: Candidate, target) -> Candidate:
    return Candidate(
        analysis=target.analysis,
        dulat=target.dulat,
        pos=target.pos,
        gloss=target.gloss,
        comment=candidate.comment,
    )


def _resolved_candidate(token: Token) -> Candidate | None:
    candidates = token._.resolved_candidates or token._.candidates
    if not candidates:
        return None
    return candidates[0]


class FormulaContextResolver:
    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("formula_context_events", [])
        for token in doc:
            token._.resolved_candidates = token._.candidates

        self._apply_trigram_rules(doc)
        self._apply_bigram_rules(doc)
        return doc

    def _apply_trigram_rules(self, doc: Doc) -> None:
        snapshot = [_resolved_candidate(token) for token in doc]
        for index in range(len(doc) - 2):
            first = snapshot[index]
            second = snapshot[index + 1]
            third = snapshot[index + 2]
            if first is None or second is None or third is None:
                continue
            if first.is_unresolved() or second.is_unresolved() or third.is_unresolved():
                continue
            rule = self._match_trigram_rule(
                doc[index]._.surface.strip(),
                doc[index + 1]._.surface.strip(),
                doc[index + 2]._.surface.strip(),
            )
            if rule is None:
                continue
            self._maybe_replace(
                doc[index],
                first,
                rule.first_target,
                require_variants=True,
                rule_name=(
                    f"formula-trigram:{rule.first_surface}-{rule.second_surface}-{rule.third_surface}:1"
                ),
            )
            self._maybe_replace(
                doc[index + 1],
                second,
                rule.second_target,
                require_variants=True,
                rule_name=(
                    f"formula-trigram:{rule.first_surface}-{rule.second_surface}-{rule.third_surface}:2"
                ),
            )
            self._maybe_replace(
                doc[index + 2],
                third,
                rule.third_target,
                require_variants=True,
                rule_name=(
                    f"formula-trigram:{rule.first_surface}-{rule.second_surface}-{rule.third_surface}:3"
                ),
            )

    def _apply_bigram_rules(self, doc: Doc) -> None:
        snapshot = [_resolved_candidate(token) for token in doc]
        for index in range(len(doc) - 1):
            first = snapshot[index]
            second = snapshot[index + 1]
            if first is None or second is None:
                continue
            if first.is_unresolved() or second.is_unresolved():
                continue
            rule = self._match_bigram_rule(
                doc[index]._.surface.strip(),
                doc[index + 1]._.surface.strip(),
            )
            if rule is None:
                continue
            self._maybe_replace(
                doc[index],
                first,
                rule.first_target,
                require_variants=False,
                allow_build=rule.allow_first_build,
                rule_name=f"formula-bigram:{rule.first_surface}-{rule.second_surface}:1",
            )
            self._maybe_replace(
                doc[index + 1],
                second,
                rule.second_target,
                require_variants=False,
                allow_build=rule.allow_second_build,
                rule_name=f"formula-bigram:{rule.first_surface}-{rule.second_surface}:2",
            )

    def _match_bigram_rule(
        self, first_surface: str, second_surface: str
    ) -> FormulaBigramRule | None:
        for rule in FORMULA_BIGRAM_RULES:
            if rule.first_surface == first_surface and rule.second_surface == second_surface:
                return rule
        return None

    def _match_trigram_rule(
        self, first_surface: str, second_surface: str, third_surface: str
    ) -> FormulaTrigramRule | None:
        for rule in FORMULA_TRIGRAM_RULES:
            if (
                rule.first_surface == first_surface
                and rule.second_surface == second_surface
                and rule.third_surface == third_surface
            ):
                return rule
        return None

    def _maybe_replace(
        self,
        token: Token,
        candidate: Candidate,
        target,
        *,
        require_variants: bool,
        allow_build: bool = False,
        rule_name: str,
    ) -> None:
        if target is None:
            return
        updated = _apply_target(candidate, target, require_variants=require_variants)
        if updated == candidate and allow_build:
            updated = _build_target(candidate, target)
        if updated == candidate:
            return
        token._.resolved_candidates = (updated,)
        token.doc.user_data["formula_context_events"].append(
            ResolutionEvent(token.i, rule_name, candidate, updated)
        )


@Language.factory("ugaritic_formula_context_resolver")
def make_formula_context_resolver(nlp, name):
    return FormulaContextResolver()
