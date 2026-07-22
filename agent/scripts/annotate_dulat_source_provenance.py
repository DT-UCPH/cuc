#!/usr/bin/env python3
"""Add non-DULAT cache-record provenance comments to reviewed TSV files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.dulat_source_provenance import (  # noqa: E402
    DulatSourceProvenanceIndex,
    append_provenance_comments,
)
from project_paths import get_project_paths  # noqa: E402


def annotate_file(path: Path, index: DulatSourceProvenanceIndex) -> int:
    """Annotate one reviewed seven- or eight-column TSV; return changed rows."""
    lines = path.read_text(encoding="utf-8").splitlines()
    data_width = next(
        (
            len(raw.split("\t"))
            for raw in lines
            if raw.split("\t", 1)[0].strip().isdigit()
        ),
        0,
    )
    has_sign_span = data_width >= 8
    dulat_index = 4 if has_sign_span else 3
    gloss_index = 6 if has_sign_span else 5
    comment_index = 7 if has_sign_span else 6
    out_lines: list[str] = []
    changed = 0
    for raw in lines:
        parts = raw.split("\t")
        if (
            not parts
            or not parts[0].strip().isdigit()
            or len(parts) <= comment_index
        ):
            out_lines.append(raw)
            continue
        sources = index.sources_for_field(parts[dulat_index], parts[gloss_index])
        updated_comment = append_provenance_comments(parts[comment_index], sources)
        if updated_comment != parts[comment_index]:
            parts[comment_index] = updated_comment
            changed += 1
            out_lines.append("\t".join(parts))
        else:
            out_lines.append(raw)
    path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return changed


def build_parser() -> argparse.ArgumentParser:
    paths = get_project_paths(REPO_ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dulat-db",
        default=str(paths.default_dulat_db()),
        help="Path to the enriched DULAT sqlite cache",
    )
    parser.add_argument(
        "--reviewed-dir",
        default=str(paths.repo_root / "reviewed"),
        help="Directory containing reviewed KTU TSV files",
    )
    parser.add_argument("--files", nargs="*", help="Optional reviewed TSV basenames")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reviewed_dir = Path(args.reviewed_dir).expanduser().resolve()
    if args.files:
        targets = [reviewed_dir / name for name in args.files]
    else:
        targets = sorted(reviewed_dir.glob("KTU *.tsv"))
    index = DulatSourceProvenanceIndex.from_sqlite(Path(args.dulat_db))
    changed = sum(annotate_file(path, index) for path in targets)
    print(f"Annotated {changed} rows in {len(targets)} reviewed TSV files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
