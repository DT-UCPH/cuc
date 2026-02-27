"""Post-verb pass: unwrap semicolon-packed variants introduced by late steps."""

from __future__ import annotations

from pipeline.steps.unwrapped_duplicate_pruner import UnwrappedDuplicatePruner
from pipeline.steps.variant_row_unwrapper import VariantRowUnwrapper


class PostVerbVariantRowUnwrapper(VariantRowUnwrapper):
    @property
    def name(self) -> str:
        return "variant-row-unwrapper-post-verb"


class PostVerbUnwrappedDuplicatePruner(UnwrappedDuplicatePruner):
    @property
    def name(self) -> str:
        return "unwrapped-duplicate-pruner-post-verb"
