"""Sort per-row parsing options by DULAT attestation frequency."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.dulat_attestation_index import DulatAttestationIndex
from pipeline.steps.base import RefinementStep, TabletRow


def _split_variants(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


@dataclass(frozen=True)
class _VariantOption:
    """Aligned variant payload for one option index."""

    source_index: int
    attestation_count: int
    analysis: str
    dulat: str
    pos: str
    gloss: str


class AttestationSortFixer(RefinementStep):
    """Sort aligned col3-col6 options by attestation count descending."""

    def __init__(self, index: DulatAttestationIndex) -> None:
        self._index = index

    @property
    def name(self) -> str:
        return "attestation-sort"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analyses = _split_variants(row.analysis)
        if len(analyses) <= 1:
            return row

        dulat = _split_variants(row.dulat)
        pos = _split_variants(row.pos)
        gloss = _split_variants(row.gloss)
        n = len(analyses)
        if len(dulat) != n or len(pos) != n or len(gloss) != n:
            return row

        options = [
            _VariantOption(
                source_index=i,
                attestation_count=self._index.count_for_variant_token(dulat[i]),
                analysis=analyses[i],
                dulat=dulat[i],
                pos=pos[i],
                gloss=gloss[i],
            )
            for i in range(n)
        ]
        sorted_options = sorted(
            options,
            key=lambda item: (-item.attestation_count, item.source_index),
        )
        if [item.source_index for item in sorted_options] == list(range(n)):
            return row

        comment = row.comment
        if comment and ";" in comment:
            comment_variants = _split_variants(comment)
            if len(comment_variants) == n:
                comment = ";".join(comment_variants[item.source_index] for item in sorted_options)

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(item.analysis for item in sorted_options),
            dulat=";".join(item.dulat for item in sorted_options),
            pos=";".join(item.pos for item in sorted_options),
            gloss=";".join(item.gloss for item in sorted_options),
            comment=comment,
        )
