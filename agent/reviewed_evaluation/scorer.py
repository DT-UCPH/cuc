"""Set-based agreement scoring for reviewed vs automatic morphology parses."""

from __future__ import annotations

from .models import (
    AggregateComparison,
    FileComparison,
    MetricSummary,
    MorphologyDataset,
    PerIdAgreement,
)


class MorphologyAgreementScorer:
    """Score morphology-column agreement against reviewed token ids."""

    def score_file_pair(
        self,
        *,
        label: str,
        reviewed: MorphologyDataset,
        auto: MorphologyDataset,
    ) -> FileComparison:
        reviewed_ids = tuple(reviewed.tokens_by_id.keys())
        auto_ids = set(auto.tokens_by_id.keys())
        missing_auto_ids = tuple(token_id for token_id in reviewed_ids if token_id not in auto_ids)
        extra_auto_ids = tuple(
            token_id
            for token_id in auto.tokens_by_id.keys()
            if token_id not in reviewed.tokens_by_id
        )

        per_id: list[PerIdAgreement] = []
        surface_mismatch_ids: list[str] = []
        for token_id in reviewed_ids:
            reviewed_token = reviewed.tokens_by_id[token_id]
            auto_token = auto.tokens_by_id.get(token_id)
            if auto_token is not None and auto_token.surface != reviewed_token.surface:
                surface_mismatch_ids.append(token_id)
            per_id.append(self._score_token(reviewed_token, auto_token))

        return FileComparison(
            label=label,
            reviewed_path=reviewed.source_path,
            auto_path=auto.source_path,
            reviewed_token_count=reviewed.token_count,
            auto_token_count=auto.token_count,
            missing_auto_ids=missing_auto_ids,
            extra_auto_ids=extra_auto_ids,
            surface_mismatch_ids=tuple(surface_mismatch_ids),
            summary=self._summarize(per_id),
            unambiguous_summary=self._summarize_optional(
                [item for item in per_id if len(item.reviewed_analyses) == 1]
            ),
            ambiguous_summary=self._summarize_optional(
                [item for item in per_id if len(item.reviewed_analyses) > 1]
            ),
            per_id=tuple(per_id),
        )

    def score_many(
        self,
        *,
        reviewed_root,
        auto_root,
        file_results: list[FileComparison],
    ) -> AggregateComparison:
        all_per_id = [item for result in file_results for item in result.per_id]
        return AggregateComparison(
            reviewed_root=reviewed_root,
            auto_root=auto_root,
            file_results=tuple(file_results),
            summary=self._summarize(all_per_id),
            unambiguous_summary=self._summarize_optional(
                [item for item in all_per_id if len(item.reviewed_analyses) == 1]
            ),
            ambiguous_summary=self._summarize_optional(
                [item for item in all_per_id if len(item.reviewed_analyses) > 1]
            ),
        )

    @staticmethod
    def _score_token(reviewed_token, auto_token) -> PerIdAgreement:
        reviewed_analyses = tuple(sorted(reviewed_token.analyses))
        auto_set = auto_token.analyses if auto_token is not None else frozenset()
        auto_analyses = tuple(sorted(auto_set))
        shared = reviewed_token.analyses & auto_set
        missing = reviewed_token.analyses - auto_set
        extra = auto_set - reviewed_token.analyses
        reviewed_count = len(reviewed_token.analyses)
        auto_count = len(auto_set)
        shared_count = len(shared)
        union_count = len(reviewed_token.analyses | auto_set)

        if auto_count == 0:
            precision = 1.0 if reviewed_count == 0 else 0.0
        else:
            precision = shared_count / auto_count
        recall = 1.0 if reviewed_count == 0 else shared_count / reviewed_count
        if reviewed_count == 0 and auto_count == 0:
            f1 = 1.0
            jaccard = 1.0
        else:
            f1 = (2 * shared_count) / (reviewed_count + auto_count)
            jaccard = shared_count / union_count if union_count else 1.0

        return PerIdAgreement(
            token_id=reviewed_token.token_id,
            surface=reviewed_token.surface,
            ref=reviewed_token.ref,
            reviewed_analyses=reviewed_analyses,
            auto_analyses=auto_analyses,
            missing_analyses=tuple(sorted(missing)),
            extra_analyses=tuple(sorted(extra)),
            exact_set_match=reviewed_token.analyses == auto_set,
            precision=precision,
            recall=recall,
            f1=f1,
            jaccard=jaccard,
            coverage=not missing,
            extra_count=len(extra),
            missing_count=len(missing),
            option_count_error=abs(reviewed_count - auto_count),
        )

    def _summarize_optional(self, per_id: list[PerIdAgreement]) -> MetricSummary | None:
        if not per_id:
            return None
        return self._summarize(per_id)

    @staticmethod
    def _summarize(per_id: list[PerIdAgreement]) -> MetricSummary:
        if not per_id:
            return MetricSummary(
                compared_ids=0,
                reviewed_option_count=0,
                auto_option_count=0,
                true_positive_option_count=0,
                exact_set_accuracy=0.0,
                macro_precision=0.0,
                macro_recall=0.0,
                macro_f1=0.0,
                macro_jaccard=0.0,
                micro_precision=0.0,
                micro_recall=0.0,
                micro_f1=0.0,
                gold_coverage=0.0,
                mean_extra_options=0.0,
                mean_missing_options=0.0,
                mean_option_count_error=0.0,
            )

        reviewed_option_count = sum(len(item.reviewed_analyses) for item in per_id)
        auto_option_count = sum(len(item.auto_analyses) for item in per_id)
        true_positive_option_count = sum(
            len(set(item.reviewed_analyses) & set(item.auto_analyses)) for item in per_id
        )

        micro_precision = (
            true_positive_option_count / auto_option_count if auto_option_count else 0.0
        )
        micro_recall = (
            true_positive_option_count / reviewed_option_count if reviewed_option_count else 0.0
        )
        if reviewed_option_count == 0 and auto_option_count == 0:
            micro_f1 = 1.0
        elif reviewed_option_count + auto_option_count == 0:
            micro_f1 = 0.0
        else:
            micro_f1 = (2 * true_positive_option_count) / (
                reviewed_option_count + auto_option_count
            )

        count = len(per_id)
        return MetricSummary(
            compared_ids=count,
            reviewed_option_count=reviewed_option_count,
            auto_option_count=auto_option_count,
            true_positive_option_count=true_positive_option_count,
            exact_set_accuracy=sum(1.0 for item in per_id if item.exact_set_match) / count,
            macro_precision=sum(item.precision for item in per_id) / count,
            macro_recall=sum(item.recall for item in per_id) / count,
            macro_f1=sum(item.f1 for item in per_id) / count,
            macro_jaccard=sum(item.jaccard for item in per_id) / count,
            micro_precision=micro_precision,
            micro_recall=micro_recall,
            micro_f1=micro_f1,
            gold_coverage=sum(1.0 for item in per_id if item.coverage) / count,
            mean_extra_options=sum(item.extra_count for item in per_id) / count,
            mean_missing_options=sum(item.missing_count for item in per_id) / count,
            mean_option_count_error=sum(item.option_count_error for item in per_id) / count,
        )
