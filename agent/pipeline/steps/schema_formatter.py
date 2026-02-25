"""Format TSV schema for labeled output files.

Responsibilities:
- enforce canonical header row for 7-column schema
- normalize separator lines to '# KTU ...'
- keep separator rows in 7-column TSV shape
- enforce exactly 7 tab-separated columns for data rows
- normalize embedded double quotes to single quotes for GitHub rendering
"""

import re
from pathlib import Path

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    is_separator_line,
    normalize_separator_line,
)

HEADER_COLUMNS = [
    "id",
    "surface form",
    "morphological parsing",
    "DULAT",
    "POS",
    "gloss",
    "comments",
]
HEADER_ROW = "\t".join(HEADER_COLUMNS)
HEADER_COLUMNS_LOWER = [value.lower() for value in HEADER_COLUMNS]
_RFC_QUOTED_FIELD_RE = re.compile(r'^"(?:[^"]|"")*"$')
_SEMICOLON_VARIANT_RE = re.compile(r"\s*;\s*(?=\S)")
_COMMA_VARIANT_RE = re.compile(r",\s*(?=\S)")


class TsvSchemaFormatter(RefinementStep):
    """Normalize labeled TSV structure without changing linguistic payload."""

    @property
    def name(self) -> str:
        return "tsv-schema"

    def refine_row(self, row):  # pragma: no cover - file-level formatter
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        rows_processed = 0
        rows_changed = 0
        header_found = False

        for raw in lines:
            if self._is_header_row(raw):
                header_found = True
                if raw != HEADER_ROW:
                    rows_changed += 1
                continue

            if not raw.strip():
                out_lines.append(raw)
                continue

            if is_separator_line(raw):
                normalized_sep = normalize_separator_line(raw)
                normalized_sep_row = "\t".join([normalized_sep] + [""] * 6)
                if normalized_sep_row != raw:
                    rows_changed += 1
                out_lines.append(normalized_sep_row)
                continue

            parts = raw.split("\t")
            if self._is_header_like_junk_row(parts):
                rows_changed += 1
                continue
            line_id = (parts[0] if parts else "").strip()
            if not line_id or not line_id[0].isdigit():
                out_lines.append(raw)
                continue

            rows_processed += 1
            normalized = self._normalize_columns(parts)
            if normalized != raw:
                rows_changed += 1
            out_lines.append(normalized)

        if not header_found:
            rows_changed += 1
        out_lines = [HEADER_ROW] + out_lines

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _is_header_row(self, raw: str) -> bool:
        parts = [part.strip().lower() for part in raw.split("\t")]
        return parts == HEADER_COLUMNS_LOWER

    def _is_header_like_junk_row(self, parts: list[str]) -> bool:
        if len(parts) < 2:
            return False
        first = (parts[0] or "").strip().lower()
        second = (parts[1] or "").strip().lower()
        return first == "id" and second == "surface form"

    def _normalize_columns(self, parts: list[str]) -> str:
        if len(parts) < 7:
            fixed = parts + [""] * (7 - len(parts))
        elif len(parts) > 7:
            merged_comment = " ".join(p.strip() for p in parts[6:] if p.strip())
            fixed = parts[:6] + [merged_comment]
        else:
            fixed = parts

        # Keep variant separators readable in structured columns:
        # "a;b" -> "a; b", "x,y" -> "x, y".
        for index in (2, 3, 4, 5):
            fixed[index] = self._normalize_variant_divider_spacing(fixed[index])

        escaped = [self._escape_field(part) for part in fixed]
        return "\t".join(escaped)

    def _normalize_variant_divider_spacing(self, value: str) -> str:
        if not value:
            return value
        normalized = _SEMICOLON_VARIANT_RE.sub("; ", value)
        normalized = _COMMA_VARIANT_RE.sub(", ", normalized)
        return normalized.strip()

    def _escape_field(self, value: str) -> str:
        # Canonicalize legacy escaping.
        normalized = value.replace('\\"', '"')

        if _RFC_QUOTED_FIELD_RE.fullmatch(normalized):
            inner = normalized[1:-1]
            while '""' in inner:
                inner = inner.replace('""', '"')
        else:
            inner = normalized
            # Previous passes may leave doubled quotes as literal text.
            while '""' in inner:
                inner = inner.replace('""', '"')

        # GitHub's TSV renderer is fragile around quoting; keep text quote-free.
        inner = inner.replace('"', "'")
        if "\t" in inner:
            return '"' + inner.replace('"', '""') + '"'
        return inner
