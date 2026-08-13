#!/usr/bin/env python3
"""Append auto-parse seed rows to an existing reviewed tablet, from a given
column onward, preserving the hand-curated rows already in the file.

Unlike build_reviewed_from_auto.py (which rewrites a whole tablet in the older
7-column layout) this emits the current 8-column reviewed layout including the
Text-Fabric `sign span`, and never touches rows already present.

Every appended row is marked `SEEDED` in the comments column so seeded content
never masquerades as reviewed. Curation removes the marker. The marker sits
behind a `##`, which keeps it out of the text published to corpus users while
leaving it machine-detectable.

Usage:
    seed_reviewed_column_range.py 1.14 III            # from column III to the end
    seed_reviewed_column_range.py 1.14 III --dry-run
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from linter.lint import (  # noqa: E402
    normalize_surface as N,
)
from linter.lint import (  # noqa: E402
    reconstruct_surface_from_analysis as RC,
)
from project_paths import get_project_paths  # noqa: E402

SEED_MARK = "## SEEDED from auto-parse; not yet hand-reviewed."
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
HDR = re.compile(r"^# KTU (\S+)(?: ([IVX]+):| )(\d+)")
_SPACING = re.compile(r"^([^\s(]+)\(([IVXLC]+)\)$")


def fix_col4(value: str) -> str:
    return "; ".join(_SPACING.sub(r"\1 (\2)", t.strip()) for t in value.split(";"))


def reconstructs(ana: str, surf: str) -> bool:
    if (ana or "").strip() in ("", "?"):
        return False
    try:
        return N(RC(ana)) == N(surf)
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tablet")
    ap.add_argument(
        "column",
        help="first column to seed, e.g. III; use '-' for a columnless tablet",
    )
    ap.add_argument("--version", default="0.2.8")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    paths = get_project_paths()
    repo = paths.repo_root
    auto_path = repo / "auto_parsing" / args.version / f"KTU {args.tablet}.tsv"
    gen_path = (
        paths.generated_sources_dir / "cuc_tablets_tsv" / args.version / f"KTU {args.tablet}.tsv"
    )
    rev_path = repo / "reviewed" / f"KTU {args.tablet}.tsv"
    for p in (auto_path, gen_path, rev_path):
        if not p.exists():
            raise SystemExit(f"missing: {p}")

    if args.column not in ROMAN and args.column != "-":
        raise SystemExit(f"unknown column {args.column}")
    start = ROMAN.index(args.column) if args.column in ROMAN else -1

    # TF sign spans
    spans = {}
    for raw in gen_path.read_text(encoding="utf-8").splitlines():
        f = raw.split("\t")
        if len(f) >= 4 and f[0].isdigit():
            spans[f[0]] = f[3]

    existing = {
        raw.split("\t")[0]
        for raw in rev_path.read_text(encoding="utf-8").splitlines()
        if raw.split("\t")[0].isdigit()
    }

    order, seen, variants, surf = [], set(), collections.defaultdict(list), {}
    loc = None
    for raw in auto_path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("#"):
            m = HDR.match(raw)
            if not m:
                continue
            col = m.group(2) or ""
            loc = (ROMAN.index(col) if col in ROMAN else -1, raw.rstrip("\t"))
            if loc[0] >= start:
                order.append(("H", loc[1]))
            continue
        f = raw.split("\t")
        if not (len(f) >= 6 and f[0].strip().isdigit() and loc and loc[0] >= start):
            continue
        tid = f[0].strip()
        variants[tid].append(tuple(f[1:6]))
        surf[tid] = f[1]
        if tid not in seen:
            seen.add(tid)
            order.append(("T", tid))

    def choose(tid):
        vs = variants[tid]
        recon = [v for v in vs if reconstructs(v[1], surf[tid])]
        pool = recon or vs
        with_entry = [v for v in pool if v[2].strip() not in ("", "?")]
        return (with_entry or pool)[0]

    out, need, skipped = [], [], 0
    for kind, val in order:
        if kind == "H":
            out.append(val + "\t" * 7)
            continue
        tid = val
        if tid in existing:
            skipped += 1
            continue
        s, ana, dulat, pos, gloss = choose(tid)
        col4 = fix_col4(dulat)
        out.append("\t".join([tid, s, spans.get(tid, ""), ana, col4, pos, gloss, SEED_MARK]))
        if not reconstructs(ana, s) or col4 == "?":
            need.append((tid, s, ana, col4, pos))

    seeded = sum(1 for line in out if line.split("\t")[0].isdigit())
    print(
        f"KTU {args.tablet} from column {args.column}: {seeded} rows to append "
        f"({skipped} already present, left untouched)"
    )
    missing_spans = sum(
        1 for line in out if line.split("\t")[0].isdigit() and not line.split("\t")[2]
    )
    print(f"  missing sign span: {missing_spans}")
    print(f"  rows needing hand review (no reconstructing variant, or col4=?): {len(need)}")
    for r in need[:40]:
        print("   ", r)
    if len(need) > 40:
        print(f"    … +{len(need) - 40} more")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    with rev_path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"\nappended to {rev_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
