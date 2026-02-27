"""Force `k(III)` for selected high-frequency verb-leading bigrams."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pipeline.config.k_functor_bigram_surfaces import K_FUNCTOR_VERB_BIGRAM_SURFACES
from pipeline.config.l_negation_exception_refs import extract_separator_ref
from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line


def _is_k_iii_row(row: TabletRow) -> bool:
    return (
        row.surface.strip() == "k"
        and row.analysis.strip() == "k(III)"
        and row.dulat.strip() == "k (III)"
    )


def _forced_k_iii_row(source: TabletRow) -> TabletRow:
    return TabletRow(
        line_id=source.line_id,
        surface=source.surface,
        analysis="k(III)",
        dulat="k (III)",
        pos="Subordinating or completive functor",
        gloss="when",
        comment=source.comment,
    )


@dataclass(frozen=True)
class _TokenGroup:
    key: tuple[str, str]
    indexes: list[int]
    rows: list[TabletRow]


class KFunctorBigramContextDisambiguator(RefinementStep):
    """Collapse ambiguous `k` to `k(III)` before selected verbal bigram heads."""

    @property
    def name(self) -> str:
        return "k-functor-bigram-context"

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
            if group.key[1] != "k":
                continue
            next_group = groups[idx + 1] if idx + 1 < len(groups) else None
            if next_group is None:
                continue
            if next_group.key[1] not in K_FUNCTOR_VERB_BIGRAM_SURFACES:
                continue
            next_has_verb = any("vb" in (row.pos or "") for row in next_group.rows)
            if not next_has_verb:
                continue

            k_target_indexes = [
                row_index for row_index, row in zip(group.indexes, group.rows) if _is_k_iii_row(row)
            ]
            keep_index = k_target_indexes[0] if k_target_indexes else group.indexes[0]
            if not k_target_indexes:
                replace_rows[keep_index] = _forced_k_iii_row(parsed_rows[keep_index])
            remove_indexes.update(
                row_index for row_index in group.indexes if row_index != keep_index
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
