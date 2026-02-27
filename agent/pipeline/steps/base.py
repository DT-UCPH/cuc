"""Base class and shared types for pipeline refinement steps."""

import abc
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

_SEPARATOR_RE = re.compile(r"^\s*#\s*(?:-+\s*)?(KTU\s+.+?)\s*$")


@dataclass
class TabletRow:
    """One parsed row from a tablet TSV file."""

    line_id: str
    surface: str
    analysis: str
    dulat: str
    pos: str
    gloss: str
    comment: str

    def to_tsv(self) -> str:
        parts = [
            self.line_id,
            self.surface,
            self.analysis,
            self.dulat,
            self.pos,
            self.gloss,
            self.comment,
        ]
        return "\t".join(parts)


@dataclass(frozen=True)
class StepResult:
    """Summary of a single step's run on one file."""

    file: str
    rows_processed: int
    rows_changed: int


def parse_tsv_line(raw: str) -> Optional[TabletRow]:
    """Parse a non-separator TSV line into a TabletRow, or None on failure."""
    parts = raw.split("\t")
    if len(parts) < 2:
        return None
    line_id = parts[0].strip()
    if not line_id or not line_id[0].isdigit():
        return None
    return TabletRow(
        line_id=line_id,
        surface=(parts[1] if len(parts) > 1 else "").strip(),
        analysis=(parts[2] if len(parts) > 2 else "").strip(),
        dulat=(parts[3] if len(parts) > 3 else "").strip(),
        pos=(parts[4] if len(parts) > 4 else "").strip(),
        gloss=(parts[5] if len(parts) > 5 else "").strip(),
        comment="\t".join(parts[6:]).strip() if len(parts) > 6 else "",
    )


def is_separator_line(raw: str) -> bool:
    """Check if a line is a CUC separator (starts with #)."""
    return raw.lstrip().startswith("#")


def normalize_separator_line(raw: str) -> str:
    """Normalize separator to compact form: '# KTU ...'."""
    m = _SEPARATOR_RE.match(raw or "")
    if not m:
        return raw
    return f"# {m.group(1)}"


def normalize_separator_row(raw: str) -> str:
    """Normalize separator while preserving existing TSV column count."""
    parts = raw.split("\t")
    normalized = normalize_separator_line(parts[0] if parts else raw)
    if len(parts) <= 1:
        return normalized
    return "\t".join([normalized] + [""] * (len(parts) - 1))


def is_unresolved(row: TabletRow) -> bool:
    """Check if a row is fully unresolved (all ? markers)."""
    return row.analysis.strip() == "?"


class RefinementStep(abc.ABC):
    """Abstract base for a single pipeline refinement step."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable step name."""

    @abc.abstractmethod
    def refine_row(self, row: TabletRow) -> TabletRow:
        """Apply this step's refinement to one row. Returns modified or original row."""

    def refine_file(self, path: Path) -> StepResult:
        """Apply this step to all data rows in a TSV file. Writes back in-place."""
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: List[str] = []
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

            if is_unresolved(row):
                out_lines.append(raw)
                rows_processed += 1
                continue

            rows_processed += 1
            refined = self.refine_row(row)
            new_line = refined.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def refine_files(self, paths: List[Path]) -> List[StepResult]:
        """Apply this step across multiple files."""
        return [self.refine_file(p) for p in paths]
