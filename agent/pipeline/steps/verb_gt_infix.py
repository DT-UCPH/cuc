"""Repair secure Gt analyses that omit the infixed ``]t]`` marker."""

from __future__ import annotations

from pathlib import Path

from morph_features.dulat_feature_reader import DulatFeatureReader
from morph_features.verbal_completion import VerbalFeatureCompleter, rewrite_row
from pipeline.steps.base import RefinementStep, TabletRow


class VerbGtInfixFixer(RefinementStep):
    """Regenerate only firm Gt rows whose analysis lacks ``]t]``."""

    def __init__(self, dulat_db: Path) -> None:
        self._completer = VerbalFeatureCompleter(DulatFeatureReader(db_path=dulat_db))

    @property
    def name(self) -> str:
        return "verb-gt-infix"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if not self._completer.needs_firm_gt_infix_repair(row):
            return row
        return rewrite_row(row, self._completer)
