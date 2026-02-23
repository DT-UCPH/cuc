"""Apply surface-keyed parsing overrides from a TSV source file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)


@dataclass(frozen=True)
class GenericOverride:
    analysis: str = ""
    dulat: str = ""
    pos: str = ""
    gloss: str = ""
    comment: str = ""


class GenericParsingOverrideFixer(RefinementStep):
    """Override per-surface parsing payload from a curated TSV file."""

    def __init__(
        self,
        overrides_path: Path | None = None,
        overrides: Mapping[str, GenericOverride] | None = None,
    ) -> None:
        self._overrides_path = overrides_path or Path("data/generic_parsing_overrides.tsv")
        if overrides is not None:
            self._overrides = {
                key.strip(): value for key, value in overrides.items() if key.strip()
            }
        else:
            self._overrides = self._load_overrides(self._overrides_path)

    @property
    def name(self) -> str:
        return "generic-parsing-override"

    def refine_row(self, row: TabletRow) -> TabletRow:
        entry = self._overrides.get(row.surface.strip())
        if not entry:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=entry.analysis or row.analysis,
            dulat=entry.dulat or row.dulat,
            pos=entry.pos or row.pos,
            gloss=entry.gloss or row.gloss,
            comment=entry.comment or row.comment,
        )

    def refine_file(self, path: Path) -> StepResult:
        """Apply overrides to all parsable data rows, including unresolved rows."""
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
            refined = self.refine_row(row)
            new_line = refined.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _load_overrides(self, path: Path) -> Dict[str, GenericOverride]:
        if not path.exists():
            return {}
        out: Dict[str, GenericOverride] = {}
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, raw in enumerate(lines):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if index == 0 and line.lower().startswith("surface form\t"):
                continue
            parts = raw.split("\t")
            while len(parts) < 6:
                parts.append("")
            surface = parts[0].strip()
            if not surface:
                continue
            out[surface] = GenericOverride(
                analysis=parts[1].strip(),
                dulat=parts[2].strip(),
                pos=parts[3].strip(),
                gloss=parts[4].strip(),
                comment=parts[5].strip(),
            )
        return out
