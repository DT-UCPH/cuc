"""Collapse ambiguous token groups when one DULAT option matches section reference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.config.l_negation_exception_refs import extract_separator_ref
from pipeline.dulat_attestation_index import DulatAttestationIndex, parse_dulat_head_token
from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line


@dataclass(frozen=True)
class _TokenGroup:
    key: tuple[str, str]
    section_ref: str
    indexes: list[int]
    rows: list[TabletRow]


def _append_comment(existing: str, note: str) -> str:
    current = (existing or "").strip()
    if not current:
        return note
    if note in current:
        return current
    return f"{current} | {note}"


class AttestationReferenceDisambiguator(RefinementStep):
    """Use DULAT references to collapse row-level ambiguities conservatively."""

    def __init__(self, index: DulatAttestationIndex) -> None:
        self._index = index

    @property
    def name(self) -> str:
        return "attestation-reference-disambiguator"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        parsed_rows: dict[int, TabletRow] = {}
        section_refs: dict[int, str] = {}
        data_indexes: list[int] = []
        active_ref = ""

        for index, raw in enumerate(lines):
            separator_ref = extract_separator_ref(raw)
            if separator_ref is not None:
                active_ref = separator_ref
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            parsed_rows[index] = row
            section_refs[index] = active_ref
            data_indexes.append(index)

        groups = self._group_rows(
            data_indexes=data_indexes,
            parsed_rows=parsed_rows,
            section_refs=section_refs,
        )
        remove_indexes: set[int] = set()
        updated_rows: dict[int, TabletRow] = {}

        for group in groups:
            if len(group.rows) <= 1:
                continue
            if not group.section_ref:
                continue

            matching_indexes_by_head: dict[tuple[str, str], list[int]] = {}
            for row_index, row in zip(group.indexes, group.rows):
                if not self._index.has_reference_for_variant_token(row.dulat, group.section_ref):
                    continue
                head_key = parse_dulat_head_token(row.dulat)
                if not head_key[0]:
                    continue
                matching_indexes_by_head.setdefault(head_key, []).append(row_index)

            if len(matching_indexes_by_head) != 1:
                continue
            keep_indexes = next(iter(matching_indexes_by_head.values()))
            note = f"DULAT direct ref {group.section_ref}"
            for row_index in keep_indexes:
                row = parsed_rows[row_index]
                updated_rows[row_index] = TabletRow(
                    line_id=row.line_id,
                    surface=row.surface,
                    analysis=row.analysis,
                    dulat=row.dulat,
                    pos=row.pos,
                    gloss=row.gloss,
                    comment=_append_comment(row.comment, note),
                )
            remove_indexes.update(
                row_index for row_index in group.indexes if row_index not in keep_indexes
            )

        if not remove_indexes and not updated_rows:
            return StepResult(file=path.name, rows_processed=len(data_indexes), rows_changed=0)

        out_lines: list[str] = []
        rows_changed = 0
        for index, raw in enumerate(lines):
            if index in remove_indexes:
                rows_changed += 1
                continue
            if index in updated_rows:
                new_line = updated_rows[index].to_tsv()
                if new_line != raw:
                    rows_changed += 1
                out_lines.append(new_line)
                continue
            out_lines.append(raw)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(
            file=path.name,
            rows_processed=len(data_indexes),
            rows_changed=rows_changed,
        )

    def _group_rows(
        self,
        data_indexes: list[int],
        parsed_rows: dict[int, TabletRow],
        section_refs: dict[int, str],
    ) -> list[_TokenGroup]:
        groups: list[_TokenGroup] = []
        current_key: tuple[str, str] | None = None
        current_section_ref = ""
        current_indexes: list[int] = []
        current_rows: list[TabletRow] = []

        for index in data_indexes:
            row = parsed_rows[index]
            key = (row.line_id.strip(), row.surface.strip())
            if current_key is None or key == current_key:
                current_key = key
                if not current_indexes:
                    current_section_ref = section_refs.get(index, "")
                current_indexes.append(index)
                current_rows.append(row)
                continue

            groups.append(
                _TokenGroup(
                    key=current_key,
                    section_ref=current_section_ref,
                    indexes=current_indexes,
                    rows=current_rows,
                )
            )
            current_key = key
            current_section_ref = section_refs.get(index, "")
            current_indexes = [index]
            current_rows = [row]

        if current_key is not None:
            groups.append(
                _TokenGroup(
                    key=current_key,
                    section_ref=current_section_ref,
                    indexes=current_indexes,
                    rows=current_rows,
                )
            )
        return groups
