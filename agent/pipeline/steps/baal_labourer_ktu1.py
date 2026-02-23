"""Remove bʕl(I) 'labourer' reading from KTU 1.* bˤl rows.

Project rule:
- bʕl(I) "labourer" is restricted to KTU 4.* attestations.
- In KTU 1.* rows with bˤl surface, keep bʕl(II) and verbal /b-ʕ-l/ readings.
"""

from pathlib import Path

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    is_unresolved,
    parse_tsv_line,
)

_TARGET_ANALYSIS = "bˤl(II)/;bˤl(I)/;bˤl["
_TARGET_DULAT = "bʕl (II);bʕl (I);/b-ʕ-l/"
_TARGET_POS = "n. m./DN;n. m.;vb"
_TARGET_GLOSS = "Baʿlu;labourer;to make"

_REPLACEMENT_ANALYSIS = "bˤl(II)/;bˤl["
_REPLACEMENT_DULAT = "bʕl (II);/b-ʕ-l/"
_REPLACEMENT_POS = "n. m./DN;vb"
_REPLACEMENT_GLOSS = "Baʿlu;to make"


class BaalLabourerKtu1Fixer(RefinementStep):
    """Drop the bʕl(I) labourer variant from KTU 1.* bˤl ambiguity rows."""

    @property
    def name(self) -> str:
        return "baal-labourer-ktu1"

    def refine_row(self, row: TabletRow) -> TabletRow:
        # Path-aware filtering is handled in refine_file.
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        rows_processed = 0
        rows_changed = 0

        is_ktu1 = path.name.startswith("KTU 1.")

        for raw in lines:
            if is_separator_line(raw) or not raw.strip():
                out_lines.append(raw)
                continue

            row = parse_tsv_line(raw)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            if is_unresolved(row):
                out_lines.append(raw)
                continue

            if is_ktu1 and self._is_target_row(row):
                refined = TabletRow(
                    line_id=row.line_id,
                    surface=row.surface,
                    analysis=_REPLACEMENT_ANALYSIS,
                    dulat=_REPLACEMENT_DULAT,
                    pos=_REPLACEMENT_POS,
                    gloss=_REPLACEMENT_GLOSS,
                    comment=row.comment,
                )
            else:
                refined = row

            new_line = refined.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _is_target_row(self, row: TabletRow) -> bool:
        return (
            row.surface.strip() == "bˤl"
            and row.analysis.strip() == _TARGET_ANALYSIS
            and row.dulat.strip() == _TARGET_DULAT
            and row.pos.strip() == _TARGET_POS
            and row.gloss.strip() == _TARGET_GLOSS
        )
