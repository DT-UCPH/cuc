"""Explode semicolon-packed col3-col6 variants into one row per option."""

from __future__ import annotations

from pathlib import Path

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _trim_trailing_empty_slots(values: list[str]) -> list[str]:
    out = list(values)
    while len(out) > 1 and not (out[-1] or "").strip():
        out.pop()
    return out


def _align_to_non_empty_anchor(values: list[str], anchor: list[str]) -> list[str]:
    """
    Project compact values onto non-empty anchor slots.

    Example:
      values=['when','like','yes']
      anchor=['','', 'Subordinating...', 'prep.', 'emph.']
      -> ['', '', 'when', 'like', 'yes']
    """
    if len(values) <= 1 or len(anchor) <= len(values):
        return values
    non_empty_indexes = [idx for idx, item in enumerate(anchor) if (item or "").strip()]
    if len(non_empty_indexes) != len(values):
        return values
    out = [""] * len(anchor)
    for value_index, target_index in enumerate(non_empty_indexes):
        out[target_index] = values[value_index]
    return out


def _variant_value(values: list[str], index: int) -> str:
    if index < len(values):
        return values[index]
    if len(values) == 1:
        return values[0]
    return ""


class VariantRowUnwrapper(RefinementStep):
    """Convert packed semicolon variants into one-variant rows."""

    @property
    def name(self) -> str:
        return "variant-row-unwrapper"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover - file-level step
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        rows_processed = 0
        rows_changed = 0

        for raw in lines:
            if not raw.strip():
                out_lines.append(raw)
                continue
            if is_separator_line(raw):
                out_lines.append(normalize_separator_row(raw))
                continue

            row = parse_tsv_line(raw)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            exploded = self._explode_row(row)
            exploded_lines = [item.to_tsv() for item in exploded]
            if len(exploded_lines) != 1 or exploded_lines[0] != raw:
                rows_changed += 1
            out_lines.extend(exploded_lines)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _explode_row(self, row: TabletRow) -> list[TabletRow]:
        analysis_variants = _trim_trailing_empty_slots(_split_semicolon(row.analysis))
        dulat_variants = _trim_trailing_empty_slots(_split_semicolon(row.dulat))
        pos_variants = _trim_trailing_empty_slots(_split_semicolon(row.pos))
        gloss_variants = _trim_trailing_empty_slots(_split_semicolon(row.gloss))

        if not analysis_variants:
            analysis_variants = [row.analysis.strip()]
        if not dulat_variants:
            dulat_variants = [row.dulat.strip()]
        if not pos_variants:
            pos_variants = [row.pos.strip()]
        if not gloss_variants:
            gloss_variants = [row.gloss.strip()]

        # Some legacy packed rows encode empty alignment slots in POS but not gloss.
        # In that case, map gloss values onto the non-empty POS slots to preserve
        # analysis/DULAT alignment (e.g., k variants in generic overrides).
        gloss_variants = _align_to_non_empty_anchor(gloss_variants, pos_variants)

        variant_count = max(
            len(analysis_variants), len(dulat_variants), len(pos_variants), len(gloss_variants), 1
        )

        out_rows: list[TabletRow] = []
        seen_payloads: set[tuple[str, str, str, str, str, str]] = set()
        for index in range(variant_count):
            expanded = TabletRow(
                line_id=row.line_id,
                surface=row.surface,
                analysis=_variant_value(analysis_variants, index),
                dulat=_variant_value(dulat_variants, index),
                pos=_variant_value(pos_variants, index),
                gloss=_variant_value(gloss_variants, index),
                comment=row.comment,
            )
            payload_key = (
                expanded.line_id.strip(),
                expanded.surface.strip(),
                expanded.analysis.strip(),
                expanded.dulat.strip(),
                expanded.pos.strip(),
                expanded.gloss.strip(),
            )
            if payload_key in seen_payloads:
                continue
            seen_payloads.add(payload_key)
            out_rows.append(expanded)

        return out_rows if out_rows else [row]
