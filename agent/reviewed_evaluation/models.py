"""Data models for reviewed morphology agreement scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MorphologyToken:
    """Unique token id with an unordered set of morphology analyses."""

    token_id: str
    surface: str
    ref: str
    analyses: frozenset[str]


@dataclass(frozen=True)
class MorphologyDataset:
    """Loaded morphology analyses from a reviewed or auto TSV file."""

    label: str
    source_path: Path | None
    tokens_by_id: dict[str, MorphologyToken]

    @property
    def token_count(self) -> int:
        return len(self.tokens_by_id)


@dataclass(frozen=True)
class EvaluationPair:
    """Reviewed/auto file pair to compare."""

    label: str
    reviewed_path: Path
    auto_path: Path | None


@dataclass(frozen=True)
class PerIdAgreement:
    """Agreement details for one reviewed token id."""

    token_id: str
    surface: str
    ref: str
    reviewed_analyses: tuple[str, ...]
    auto_analyses: tuple[str, ...]
    missing_analyses: tuple[str, ...]
    extra_analyses: tuple[str, ...]
    exact_set_match: bool
    precision: float
    recall: float
    f1: float
    jaccard: float
    coverage: bool
    extra_count: int
    missing_count: int
    option_count_error: int

    def to_dict(self) -> dict[str, object]:
        return {
            "token_id": self.token_id,
            "surface": self.surface,
            "ref": self.ref,
            "reviewed_analyses": list(self.reviewed_analyses),
            "auto_analyses": list(self.auto_analyses),
            "missing_analyses": list(self.missing_analyses),
            "extra_analyses": list(self.extra_analyses),
            "exact_set_match": self.exact_set_match,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "jaccard": self.jaccard,
            "coverage": self.coverage,
            "extra_count": self.extra_count,
            "missing_count": self.missing_count,
            "option_count_error": self.option_count_error,
        }


@dataclass(frozen=True)
class MetricSummary:
    """Aggregate metrics across reviewed token ids."""

    compared_ids: int
    reviewed_option_count: int
    auto_option_count: int
    true_positive_option_count: int
    exact_set_accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    macro_jaccard: float
    micro_precision: float
    micro_recall: float
    micro_f1: float
    gold_coverage: float
    mean_extra_options: float
    mean_missing_options: float
    mean_option_count_error: float

    def to_dict(self) -> dict[str, object]:
        return {
            "compared_ids": self.compared_ids,
            "reviewed_option_count": self.reviewed_option_count,
            "auto_option_count": self.auto_option_count,
            "true_positive_option_count": self.true_positive_option_count,
            "exact_set_accuracy": self.exact_set_accuracy,
            "macro_precision": self.macro_precision,
            "macro_recall": self.macro_recall,
            "macro_f1": self.macro_f1,
            "macro_jaccard": self.macro_jaccard,
            "micro_precision": self.micro_precision,
            "micro_recall": self.micro_recall,
            "micro_f1": self.micro_f1,
            "gold_coverage": self.gold_coverage,
            "mean_extra_options": self.mean_extra_options,
            "mean_missing_options": self.mean_missing_options,
            "mean_option_count_error": self.mean_option_count_error,
        }


@dataclass(frozen=True)
class FileComparison:
    """Evaluation result for one reviewed TSV against one auto TSV."""

    label: str
    reviewed_path: Path | None
    auto_path: Path | None
    reviewed_token_count: int
    auto_token_count: int
    missing_auto_ids: tuple[str, ...]
    extra_auto_ids: tuple[str, ...]
    surface_mismatch_ids: tuple[str, ...]
    summary: MetricSummary
    unambiguous_summary: MetricSummary | None
    ambiguous_summary: MetricSummary | None
    per_id: tuple[PerIdAgreement, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "reviewed_path": str(self.reviewed_path) if self.reviewed_path else None,
            "auto_path": str(self.auto_path) if self.auto_path else None,
            "reviewed_token_count": self.reviewed_token_count,
            "auto_token_count": self.auto_token_count,
            "missing_auto_ids": list(self.missing_auto_ids),
            "extra_auto_ids": list(self.extra_auto_ids),
            "surface_mismatch_ids": list(self.surface_mismatch_ids),
            "summary": self.summary.to_dict(),
            "unambiguous_summary": (
                self.unambiguous_summary.to_dict() if self.unambiguous_summary is not None else None
            ),
            "ambiguous_summary": (
                self.ambiguous_summary.to_dict() if self.ambiguous_summary is not None else None
            ),
            "per_id": [item.to_dict() for item in self.per_id],
        }


@dataclass(frozen=True)
class AggregateComparison:
    """Aggregate evaluation across multiple reviewed files."""

    reviewed_root: Path | None
    auto_root: Path | None
    file_results: tuple[FileComparison, ...]
    summary: MetricSummary
    unambiguous_summary: MetricSummary | None
    ambiguous_summary: MetricSummary | None

    def to_dict(self) -> dict[str, object]:
        return {
            "reviewed_root": str(self.reviewed_root) if self.reviewed_root else None,
            "auto_root": str(self.auto_root) if self.auto_root else None,
            "file_count": len(self.file_results),
            "summary": self.summary.to_dict(),
            "unambiguous_summary": (
                self.unambiguous_summary.to_dict() if self.unambiguous_summary is not None else None
            ),
            "ambiguous_summary": (
                self.ambiguous_summary.to_dict() if self.ambiguous_summary is not None else None
            ),
            "files": [result.to_dict() for result in self.file_results],
        }
