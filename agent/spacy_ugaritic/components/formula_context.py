"""Rule-based spaCy component for formula bigram/trigram normalization."""

from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc, Token

from pipeline.config.formula_bigram_rules import FORMULA_BIGRAM_RULES, FormulaBigramRule
from pipeline.config.formula_trigram_rules import FORMULA_TRIGRAM_RULES, FormulaTrigramRule
from pipeline.steps.base import TabletRow, is_unresolved


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: TabletRow
    after: TabletRow


def _split_variants(value: str) -> list[str]:
    return [variant.strip() for variant in (value or "").split(";") if variant.strip()]


def _target_supported(row: TabletRow, target) -> bool:
    return target.dulat in set(_split_variants(row.dulat))


def _has_variants(row: TabletRow) -> bool:
    return ";" in row.analysis or ";" in row.dulat or ";" in row.pos or ";" in row.gloss


def _apply_target(row: TabletRow, target, *, require_variants: bool) -> TabletRow:
    if not _target_supported(row, target):
        return row
    if (
        row.analysis == target.analysis
        and row.dulat == target.dulat
        and row.pos == target.pos
        and row.gloss == target.gloss
    ):
        return row
    if require_variants and not _has_variants(row):
        return row
    return TabletRow(
        line_id=row.line_id,
        surface=row.surface,
        analysis=target.analysis,
        dulat=target.dulat,
        pos=target.pos,
        gloss=target.gloss,
        comment=row.comment,
    )


class FormulaContextResolver:
    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("formula_context_events", [])
        for token in doc:
            token._.resolved_row = token._.row

        self._apply_trigram_rules(doc)
        self._apply_bigram_rules(doc)
        return doc

    def _apply_trigram_rules(self, doc: Doc) -> None:
        snapshot = [token._.resolved_row for token in doc]
        for index in range(len(doc) - 2):
            first = snapshot[index]
            second = snapshot[index + 1]
            third = snapshot[index + 2]
            if first is None or second is None or third is None:
                continue
            if is_unresolved(first) or is_unresolved(second) or is_unresolved(third):
                continue
            rule = self._match_trigram_rule(
                first.surface.strip(), second.surface.strip(), third.surface.strip()
            )
            if rule is None:
                continue
            self._maybe_replace(
                doc[index],
                first,
                rule.first_target,
                require_variants=True,
                rule_name=f"formula-trigram:{rule.first_surface}-{rule.second_surface}-{rule.third_surface}:1",
            )
            self._maybe_replace(
                doc[index + 1],
                second,
                rule.second_target,
                require_variants=True,
                rule_name=f"formula-trigram:{rule.first_surface}-{rule.second_surface}-{rule.third_surface}:2",
            )
            self._maybe_replace(
                doc[index + 2],
                third,
                rule.third_target,
                require_variants=True,
                rule_name=f"formula-trigram:{rule.first_surface}-{rule.second_surface}-{rule.third_surface}:3",
            )

    def _apply_bigram_rules(self, doc: Doc) -> None:
        snapshot = [token._.resolved_row for token in doc]
        for index in range(len(doc) - 1):
            first = snapshot[index]
            second = snapshot[index + 1]
            if first is None or second is None:
                continue
            if is_unresolved(first) or is_unresolved(second):
                continue
            rule = self._match_bigram_rule(first.surface.strip(), second.surface.strip())
            if rule is None:
                continue
            self._maybe_replace(
                doc[index],
                first,
                rule.first_target,
                require_variants=False,
                rule_name=f"formula-bigram:{rule.first_surface}-{rule.second_surface}:1",
            )
            self._maybe_replace(
                doc[index + 1],
                second,
                rule.second_target,
                require_variants=False,
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
        row: TabletRow,
        target,
        *,
        require_variants: bool,
        rule_name: str,
    ) -> None:
        if target is None:
            return
        updated = _apply_target(row, target, require_variants=require_variants)
        if updated.to_tsv() == row.to_tsv():
            return
        token._.resolved_row = updated
        token.doc.user_data["formula_context_events"].append(
            ResolutionEvent(token.i, rule_name, row, updated)
        )


@Language.factory("ugaritic_formula_context_resolver")
def make_formula_context_resolver(nlp, name):
    return FormulaContextResolver()
