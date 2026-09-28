"""Discard a rejected candidate only when the same token retains a finite one."""

from pathlib import Path

from pipeline.config.l_negation_exception_refs import extract_separator_ref
from pipeline.config.ytb_messenger_readings import rejected_messenger_participle
from pipeline.steps.base import RefinementStep, StepResult, parse_tsv_line


class YtbMessengerReadingPruner(RefinementStep):
    @property
    def name(self) -> str:
        return "ytb-messenger-reading-pruner"

    def refine_row(self, row):
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        records = []
        finite = set()
        ref = ""
        for index, raw in enumerate(lines):
            if raw.startswith("#"):
                ref = extract_separator_ref(raw.split("\t")[0]) or ""
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            key = (ref, row.line_id, row.surface)
            records.append((index, ref, key, row))
            if (
                row.dulat == "/y-ṯ-b/"
                and row.analysis not in {"", "?"}
                and ";" not in row.analysis
                and ("prefc." in row.pos or "suffc." in row.pos)
            ):
                finite.add(key)
        remove = {
            index for index, ref, key, row in records
            if key in finite
            and rejected_messenger_participle(ref, row.surface, row.analysis, row.pos)
        }
        if remove:
            path.write_text(
                "\n".join(raw for i, raw in enumerate(lines) if i not in remove) + "\n",
                encoding="utf-8",
            )
        return StepResult(path.name, len(records), len(remove))
