"""Normalize high-confidence prepositional `l + X` bigrams."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.config.l_negation_exception_refs import extract_separator_ref
from pipeline.config.l_preposition_bigram_rules import (
    L_BAAL_ANALYSIS,
    L_BAAL_DULAT,
    L_BAAL_SURFACE,
    L_FORCE_I_BIGRAM_SURFACES,
    L_PN_FAMILY_FORCE_I_SURFACES,
    L_PN_PREP_CANONICAL_PAYLOADS,
    CanonicalSecondPayload,
)
from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line


def _is_l_i_row(row: TabletRow) -> bool:
    return (
        row.surface.strip() == "l"
        and row.analysis.strip() == "l(I)"
        and row.dulat.strip() == "l (I)"
    )


def _is_baal_ii_row(row: TabletRow) -> bool:
    return (
        row.surface.strip() == L_BAAL_SURFACE
        and row.analysis.strip() == L_BAAL_ANALYSIS
        and row.dulat.strip() == L_BAAL_DULAT
    )


def _matches_payload(row: TabletRow, payload: CanonicalSecondPayload) -> bool:
    return (
        row.analysis.strip() == payload.analysis
        and row.dulat.strip() == payload.dulat
        and row.pos.strip() == payload.pos
        and row.gloss.strip() == payload.gloss
    )


def _forced_l_i_row(source: TabletRow) -> TabletRow:
    return TabletRow(
        line_id=source.line_id,
        surface=source.surface,
        analysis="l(I)",
        dulat="l (I)",
        pos="prep.",
        gloss="to",
        comment=source.comment,
    )


def _forced_second_row(source: TabletRow, payload: CanonicalSecondPayload) -> TabletRow:
    return TabletRow(
        line_id=source.line_id,
        surface=source.surface,
        analysis=payload.analysis,
        dulat=payload.dulat,
        pos=payload.pos,
        gloss=payload.gloss,
        comment=source.comment,
    )


def _is_ktu4_tablet(path: Path) -> bool:
    return path.name.startswith("KTU 4.")


@dataclass(frozen=True)
class _TokenGroup:
    key: tuple[str, str]
    indexes: list[int]
    rows: list[TabletRow]


class LPrepositionBigramContextDisambiguator(RefinementStep):
    """Force `l(I)` in high-confidence `l + X` prepositional contexts."""

    @property
    def name(self) -> str:
        return "l-preposition-bigram-context"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        parsed_rows: dict[int, TabletRow] = {}
        data_indexes: list[int] = []

        for index, raw in enumerate(lines):
            separator_ref = extract_separator_ref(raw)
            if separator_ref is not None:
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            parsed_rows[index] = row
            data_indexes.append(index)

        groups = self._group_rows(data_indexes=data_indexes, parsed_rows=parsed_rows)
        remove_indexes: set[int] = set()
        replace_rows: dict[int, TabletRow] = {}

        for idx, group in enumerate(groups):
            if group.key[1] != "l":
                continue
            next_group = groups[idx + 1] if idx + 1 < len(groups) else None
            if next_group is None:
                continue

            next_surface = next_group.key[1]
            force_l_i = False

            if next_surface in L_FORCE_I_BIGRAM_SURFACES:
                force_l_i = True

            if next_surface in L_PN_FAMILY_FORCE_I_SURFACES:
                force_l_i = True

            if next_surface == L_BAAL_SURFACE and not _is_ktu4_tablet(path):
                if any(_is_baal_ii_row(row) for row in next_group.rows):
                    force_l_i = True

            if not force_l_i:
                continue

            l_target_indexes = [
                row_index for row_index, row in zip(group.indexes, group.rows) if _is_l_i_row(row)
            ]
            keep_l_index = l_target_indexes[0] if l_target_indexes else group.indexes[0]
            forced_l = _forced_l_i_row(parsed_rows[keep_l_index])
            if forced_l.to_tsv() != parsed_rows[keep_l_index].to_tsv():
                replace_rows[keep_l_index] = forced_l
            remove_indexes.update(
                row_index for row_index in group.indexes if row_index != keep_l_index
            )

            if next_surface == L_BAAL_SURFACE and not _is_ktu4_tablet(path):
                baal_ii_indexes = [
                    row_index
                    for row_index, row in zip(next_group.indexes, next_group.rows)
                    if _is_baal_ii_row(row)
                ]
                if baal_ii_indexes:
                    keep_baal_index = next(
                        (
                            row_index
                            for row_index, row in zip(next_group.indexes, next_group.rows)
                            if row_index in baal_ii_indexes and "DN" in (row.pos or "")
                        ),
                        baal_ii_indexes[0],
                    )
                    remove_indexes.update(
                        row_index
                        for row_index in next_group.indexes
                        if row_index != keep_baal_index
                    )
                continue

            pn_payload = L_PN_PREP_CANONICAL_PAYLOADS.get(next_surface)
            if pn_payload is None:
                continue

            pn_target_indexes = [
                row_index
                for row_index, row in zip(next_group.indexes, next_group.rows)
                if _matches_payload(row, pn_payload)
            ]
            keep_second_index = pn_target_indexes[0] if pn_target_indexes else next_group.indexes[0]
            forced_second = _forced_second_row(parsed_rows[keep_second_index], pn_payload)
            if forced_second.to_tsv() != parsed_rows[keep_second_index].to_tsv():
                replace_rows[keep_second_index] = forced_second
            remove_indexes.update(
                row_index for row_index in next_group.indexes if row_index != keep_second_index
            )

        if not remove_indexes and not replace_rows:
            return StepResult(file=path.name, rows_processed=len(data_indexes), rows_changed=0)

        out_lines: list[str] = []
        for index, raw in enumerate(lines):
            if index in remove_indexes:
                continue
            replacement = replace_rows.get(index)
            out_lines.append(raw if replacement is None else replacement.to_tsv())

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(
            file=path.name,
            rows_processed=len(data_indexes),
            rows_changed=len(remove_indexes) + len(replace_rows),
        )

    def _group_rows(
        self,
        data_indexes: list[int],
        parsed_rows: dict[int, TabletRow],
    ) -> list[_TokenGroup]:
        groups: list[_TokenGroup] = []
        current_key: tuple[str, str] | None = None
        current_indexes: list[int] = []
        current_rows: list[TabletRow] = []

        for index in data_indexes:
            row = parsed_rows[index]
            key = (row.line_id.strip(), row.surface.strip())
            if current_key is None or key == current_key:
                current_key = key
                current_indexes.append(index)
                current_rows.append(row)
                continue

            groups.append(_TokenGroup(key=current_key, indexes=current_indexes, rows=current_rows))
            current_key = key
            current_indexes = [index]
            current_rows = [row]

        if current_key is not None:
            groups.append(_TokenGroup(key=current_key, indexes=current_indexes, rows=current_rows))
        return groups
