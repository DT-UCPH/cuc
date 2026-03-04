"""Deterministic verbal morphology completion and row splitting."""

from __future__ import annotations

from pathlib import Path

from morph_features.dulat_feature_reader import DulatFeatureReader
from morph_features.verbal_completion import VerbalFeatureCompleter, rewrite_row
from pipeline.steps.base import RefinementStep, TabletRow


class VerbalFeatureCompletionFixer(RefinementStep):
    """Complete verb form/person features from analysis and exact DULAT forms."""

    def __init__(self, dulat_db: Path) -> None:
        self._completer = VerbalFeatureCompleter(DulatFeatureReader(db_path=dulat_db))

    @property
    def name(self) -> str:
        return "verbal-feature-completion"

    def refine_row(self, row: TabletRow) -> TabletRow:
        return rewrite_row(row, self._completer)
