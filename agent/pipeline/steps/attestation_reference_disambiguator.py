"""Collapse ambiguous token groups when one DULAT option matches section reference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.config.l_negation_exception_refs import extract_separator_ref
from pipeline.dulat_attestation_index import DulatAttestationIndex
from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line


@dataclass(frozen=True)
class _TokenGroup:
    key: tuple[str, str]
    section_ref: str
    indexes: list[int]
    rows: list[TabletRow]


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

        for group in groups:
            if len(group.rows) <= 1:
                continue
            if not group.section_ref:
                continue

            matching_indexes = [
                row_index
                for row_index, row in zip(group.indexes, group.rows)
                if self._index.has_reference_for_variant_token(row.dulat, group.section_ref)
            ]
            if len(matching_indexes) != 1:
                continue
            keep_index = matching_indexes[0]
            remove_indexes.update(
                row_index for row_index in group.indexes if row_index != keep_index
            )

        if not remove_indexes:
            return StepResult(file=path.name, rows_processed=len(data_indexes), rows_changed=0)

        out_lines: list[str] = []
        for index, raw in enumerate(lines):
            if index in remove_indexes:
                continue
            out_lines.append(raw)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(
            file=path.name,
            rows_processed=len(data_indexes),
            rows_changed=len(remove_indexes),
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
