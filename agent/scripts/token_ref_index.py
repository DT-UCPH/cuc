#!/usr/bin/env python3
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set


@dataclass
class TokenRef:
    file: str
    line_no: int
    line_id: str
    surface: str
    ref: str


def parse_ref_header(raw: str) -> Optional[str]:
    text = raw.strip()
    if not text.startswith("#"):
        return None
    payload = text.lstrip("#- ").strip()
    if payload.startswith("KTU "):
        return payload
    return None


def iter_token_refs(path: Path) -> Iterable[TokenRef]:
    current_ref = ""
    with path.open("r", encoding="utf-8") as handle:
        for idx, raw in enumerate(handle, start=1):
            ref = parse_ref_header(raw)
            if ref is not None:
                current_ref = ref
                continue
            line = raw.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            line_id = (parts[0] or "").strip()
            if not line_id.isdigit():
                continue
            surface = (parts[1] or "").strip()
            yield TokenRef(
                file=str(path),
                line_no=idx,
                line_id=line_id,
                surface=surface,
                ref=current_ref,
            )


def discover_files(explicit: List[str], glob_pattern: str) -> List[Path]:
    if explicit:
        return [Path(p) for p in explicit]
    return sorted(Path(".").glob(glob_pattern))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index token IDs to KTU reference headers in TSV files."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="TSV files to scan. If omitted, --glob is used.",
    )
    parser.add_argument(
        "--glob",
        default="out/KTU 1.*.tsv",
        help="Glob pattern used when files are not provided.",
    )
    parser.add_argument(
        "--id",
        action="append",
        dest="ids",
        help="Line id filter (repeatable).",
    )
    parser.add_argument(
        "--surface",
        help="Surface substring filter.",
    )
    parser.add_argument(
        "--output",
        help="Optional output TSV path.",
    )
    args = parser.parse_args()

    files = discover_files(args.files, args.glob)
    rows: List[TokenRef] = []
    for path in files:
        if not path.exists():
            continue
        rows.extend(iter_token_refs(path))

    id_filter: Optional[Set[str]] = set(args.ids) if args.ids else None
    if id_filter:
        rows = [r for r in rows if r.line_id in id_filter]
    if args.surface:
        q = args.surface
        rows = [r for r in rows if q in r.surface]

    lines = ["file\tline_no\tline_id\tsurface\tref"]
    for row in rows:
        lines.append(
            f"{row.file}\t{row.line_no}\t{row.line_id}\t{row.surface}\t{row.ref}"
        )
    text = "\n".join(lines)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
