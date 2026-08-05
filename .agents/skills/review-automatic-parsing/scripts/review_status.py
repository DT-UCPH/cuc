#!/usr/bin/env python3
"""Report per-column review status for reviewed CUC tablets.

Answers "what is still unreviewed" before a session and "is this column
actually finished" after one. A column is finished when no row still carries
the seed marker and every residual `?` on a legible surface carries a comment
explaining why it stays unresolved.

`?` on a broken or empty surface is normal and expected -- most of a damaged
column is unresolvable. `?` on a legible surface with no comment is the defect
class this reports as `undocumented`.

Usage:
    review_status.py                     # every reviewed/*.tsv
    review_status.py 1.14 1.4            # named tablets
    review_status.py 1.14 --rows IV      # list the outstanding rows of a column

See ../SKILL.md.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SEED_MARK = "SEEDED from auto-parse"

# `# KTU 1.14 III:2` (columned tablet) and `# KTU 2.10 4` (uncolumned letter).
HEADER_RE = re.compile(r"^# KTU (\S+)(?: ([IVX]+):| )(\d+)")

# Reviewed layout carries an extra "sign span" column that automatic output lacks.
REVIEWED_IDX = {"id": 0, "surface": 1, "analysis": 3, "pos": 5, "comment": 7}
AUTO_IDX = {"id": 0, "surface": 1, "analysis": 2, "pos": 4, "comment": 6}


def repo_root(start: Path) -> Path:
    for cand in [start, *start.parents]:
        if (cand / "reviewed").is_dir() and (cand / "agent").is_dir():
            return cand
    raise SystemExit("run from inside the cuc-origin repo")


def field(row: list[str], idx: dict[str, int], key: str) -> str:
    pos = idx[key]
    return row[pos].strip() if len(row) > pos else ""


def is_broken(surface: str) -> bool:
    """A surface with no legible reading: fully lost, or an `x` sign placeholder."""
    return not surface or "x" in surface


def read_rows(path: Path):
    """Yield (column, row, idx) for data rows, tracking the current column."""
    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader, None)
        idx = REVIEWED_IDX if header and "sign span" in header else AUTO_IDX
        column = None
        for row in reader:
            if not row:
                continue
            marker = HEADER_RE.match(row[0])
            if marker:
                column = marker.group(2) or "-"
                continue
            if not row[0].strip().isdigit():
                continue
            yield column, row, idx


def scan(path: Path):
    """Return {column: Counter} plus the outstanding rows keyed by column."""
    stats: dict[str, Counter] = defaultdict(Counter)
    outstanding: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    ids_seen: dict[str, Counter] = defaultdict(Counter)

    for column, row, idx in read_rows(path):
        tid = field(row, idx, "id")
        surface = field(row, idx, "surface")
        analysis = field(row, idx, "analysis")
        pos = field(row, idx, "pos")
        comment = field(row, idx, "comment")

        stat = stats[column]
        ids_seen[column][tid] += 1
        if ids_seen[column][tid] == 1:
            stat["tokens"] += 1
        else:
            stat["alt_rows"] += 1

        if comment.startswith(SEED_MARK):
            # Not reviewed yet, so the `?` audit below does not apply to it.
            stat["seeded"] += 1
            outstanding[column].append((tid, surface, "seeded"))
            continue

        if analysis == "?" or pos == "?":
            if is_broken(surface):
                stat["q_broken"] += 1
            elif not comment:
                stat["q_undocumented"] += 1
                outstanding[column].append((tid, surface, "undocumented ?"))
            else:
                stat["q_documented"] += 1

    return stats, outstanding


def print_table(name: str, stats: dict[str, Counter]) -> bool:
    print(name)
    print(
        f"  {'col':<5}{'tokens':>7}{'alt':>5}{'seeded':>8}"
        f"{'?broken':>9}{'?documented':>13}{'?undocumented':>15}"
    )
    clean = True
    for column, stat in stats.items():
        flag = ""
        if stat["seeded"] or stat["q_undocumented"]:
            flag = "  <-"
            clean = False
        print(
            f"  {column or '-':<5}{stat['tokens']:>7}{stat['alt_rows']:>5}{stat['seeded']:>8}"
            f"{stat['q_broken']:>9}{stat['q_documented']:>13}{stat['q_undocumented']:>15}{flag}"
        )
    return clean


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tablets", nargs="*", help="tablet numbers, e.g. 1.14 (default: all)")
    ap.add_argument("--rows", metavar="COL", help="list outstanding rows of this column")
    args = ap.parse_args()

    root = repo_root(Path.cwd().resolve())
    reviewed = root / "reviewed"

    if args.tablets:
        paths = [reviewed / f"KTU {t}.tsv" for t in args.tablets]
        missing = [p for p in paths if not p.exists()]
        if missing:
            raise SystemExit(f"no such reviewed file: {missing[0]}")
    else:
        paths = sorted(reviewed.glob("*.tsv"))

    all_clean = True
    for path in paths:
        stats, outstanding = scan(path)
        if not print_table(path.name, stats):
            all_clean = False
        if args.rows:
            rows = outstanding.get(args.rows, [])
            print(f"\n  outstanding in column {args.rows}: {len(rows)}")
            for tid, surface, why in rows:
                print(f"    {tid:<10}{surface:<16}{why}")
        print()

    if all_clean:
        print("No seeded or undocumented-unresolved rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
