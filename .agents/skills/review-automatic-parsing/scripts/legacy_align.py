#!/usr/bin/env python3
"""Align a legacy expert review to the current reviewed TSV, by line reference.

The legacy reviews (`reviewed/*.txt`, `reviewed/orig/*.txt`) carry token ids
from an older Text-Fabric id space, so they cannot be joined on id -- that is
what made an earlier id-based certification attempt unusable. Their
`# KTU <tablet> <col>:<line>` markers and surface sequences *are* stable, so
this aligns line by line and compares only the analysis column, which is the
one the legacy files reliably fill.

Verdicts:
    AGREE       identical after legacy-notation normalization
    AGREE~      identical once homonym tags are ignored; the legacy file is
                simply less specific (legacy `ym/` vs reviewed `ym(I)/`)
    DIFFER      a real disagreement -- adjudicate it, do not assume either side
    SPLIT/JOIN  the two tokenizations disagree about word boundaries here

AGREE is corroboration, not proof: the legacy reviewer and the parser can be
wrong together. DIFFER on a seeded row is the highest-value signal in the file,
because the parser is contradicting a human reading.

Usage:
    legacy_align.py 1.14                      # whole tablet, disagreements only
    legacy_align.py 1.14 --columns IV,V,VI    # scope to the columns under review
    legacy_align.py 1.14 --all                # include agreements
    legacy_align.py 1.14 --legacy path.txt    # explicit legacy file

See ../SKILL.md.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HEADER_RE = re.compile(r"^# KTU (\S+)(?: ([IVX]+):| )(\d+)")
HOMONYM_RE = re.compile(r"\((?:I|II|III|IV|V)\)")
SEED_MARK = "SEEDED from auto-parse"

# Reviewed TSV has a "sign span" column that the legacy txt layout lacks.
REVIEWED_IDX = {"id": 0, "surface": 1, "analysis": 3, "comment": 7}
LEGACY_IDX = {"id": 0, "surface": 1, "analysis": 2, "comment": 6}


def repo_root(start: Path) -> Path:
    for cand in [start, *start.parents]:
        if (cand / "reviewed").is_dir() and (cand / "agent").is_dir():
            return cand
    raise SystemExit("run from inside the cuc-origin repo")


ROOT = repo_root(Path.cwd().resolve())
sys.path.insert(0, str(ROOT / "agent"))
from reviewed_normalization import normalize_reviewed_analysis  # noqa: E402


def normalize(analysis: str) -> str:
    return normalize_reviewed_analysis(analysis or "").strip()


def strip_homonyms(analysis: str) -> str:
    return HOMONYM_RE.sub("", analysis)


def load(path: Path, idx: dict[str, int]):
    """Return {(column, line): [(id, surface, {analyses}, seeded)]} in file order."""
    blocks: dict[tuple[str, str], list] = defaultdict(list)
    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh, delimiter="\t")
        next(reader, None)
        key = None
        by_id: dict[str, list] = {}
        for row in reader:
            if not row:
                continue
            marker = HEADER_RE.match(row[0])
            if marker:
                key = (marker.group(2) or "-", marker.group(3))
                by_id = {}
                continue
            if key is None or not row[0].strip().isdigit():
                continue

            def get(name: str) -> str:
                pos = idx[name]
                return row[pos].strip() if len(row) > pos else ""

            tid, surface = get("id"), get("surface")
            analysis, comment = normalize(get("analysis")), get("comment")
            if tid in by_id:
                # Alternative row for a token already seen on this line.
                by_id[tid][2].add(analysis)
                continue
            entry = [tid, surface, {analysis}, SEED_MARK in comment]
            by_id[tid] = entry
            blocks[key].append(entry)
    if not blocks:
        raise SystemExit(
            f"{path} has no '# KTU <tablet> <col>:<line>' markers, so it cannot be\n"
            "aligned by line reference. Files under reviewed/orig/ are bare id dumps\n"
            "without markers -- use a marked legacy file, or pass --legacy explicitly."
        )
    return blocks


def verdict(left: set[str], right: set[str]) -> str:
    left = {a for a in left if a}
    right = {a for a in right if a}
    if not left or not right:
        return "NO-ANALYSIS"
    if left == right:
        return "AGREE"
    if {strip_homonyms(a) for a in left} == {strip_homonyms(a) for a in right}:
        return "AGREE~"
    return "DIFFER"


def fmt(analyses: set[str]) -> str:
    return " | ".join(sorted(a for a in analyses if a)) or "(none)"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("tablet", help="tablet number, e.g. 1.14")
    ap.add_argument("--columns", help="comma-separated column filter, e.g. IV,V,VI")
    ap.add_argument("--legacy", help="explicit legacy file path")
    ap.add_argument("--all", action="store_true", help="list agreements too")
    ap.add_argument("--seeded-only", action="store_true", help="only rows still marked SEEDED")
    args = ap.parse_args()

    reviewed_path = ROOT / "reviewed" / f"KTU {args.tablet}.tsv"
    if not reviewed_path.exists():
        raise SystemExit(f"no reviewed TSV: {reviewed_path}")

    if args.legacy:
        legacy_path = Path(args.legacy)
    else:
        candidates = [
            ROOT / "reviewed" / f"KTU {args.tablet}.txt",
            ROOT / "reviewed" / "orig" / f"KTU {args.tablet}.txt",
        ]
        legacy_path = next((c for c in candidates if c.exists()), None)
        if legacy_path is None:
            raise SystemExit(
                f"no legacy review found for {args.tablet}; tried:\n  "
                + "\n  ".join(str(c) for c in candidates)
            )

    wanted = {c.strip().upper() for c in args.columns.split(",")} if args.columns else None

    reviewed = load(reviewed_path, REVIEWED_IDX)
    legacy = load(legacy_path, LEGACY_IDX)

    print(f"reviewed: {reviewed_path.relative_to(ROOT)}")
    print(f"legacy:   {legacy_path.relative_to(ROOT)}")
    if wanted:
        print(f"columns:  {','.join(sorted(wanted))}")
    print()

    tally: Counter = Counter()
    findings: list[str] = []

    # Every reviewed token in scope lands in exactly one of these buckets.
    scoped_tokens = 0
    absent_tokens = 0  # on a line the legacy file does not cover
    uncomparable_tokens = 0  # inside a token-boundary mismatch
    filtered_tokens = 0  # excluded by --seeded-only

    for key in sorted(reviewed, key=lambda k: (k[0], int(k[1]))):
        column, line = key
        if wanted and column not in wanted:
            continue
        rev_rows = reviewed[key]
        scoped_tokens += len(rev_rows)
        leg_rows = legacy.get(key)
        if leg_rows is None:
            tally["lines-absent-from-legacy"] += 1
            absent_tokens += len(rev_rows)
            continue

        matcher = difflib.SequenceMatcher(
            a=[r[1] for r in leg_rows], b=[r[1] for r in rev_rows], autojunk=False
        )
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                for leg, rev in zip(leg_rows[i1:i2], rev_rows[j1:j2]):
                    if args.seeded_only and not rev[3]:
                        filtered_tokens += 1
                        continue
                    result = verdict(leg[2], rev[2])
                    tally[result] += 1
                    if result in ("AGREE", "AGREE~") and not args.all:
                        continue
                    seed = " [SEEDED]" if rev[3] else ""
                    findings.append(
                        f"  {column}:{line:<4} {rev[0]:<9} {rev[1]:<14} {result:<11}{seed}\n"
                        f"      legacy   {fmt(leg[2])}\n"
                        f"      reviewed {fmt(rev[2])}"
                    )
            else:
                if args.seeded_only and not any(r[3] for r in rev_rows[j1:j2]):
                    filtered_tokens += len(rev_rows[j1:j2])
                    continue
                uncomparable_tokens += len(rev_rows[j1:j2])
                tally["SPLIT/JOIN"] += 1
                leg_surfaces = " ".join(r[1] for r in leg_rows[i1:i2]) or "(none)"
                rev_surfaces = " ".join(r[1] for r in rev_rows[j1:j2]) or "(none)"
                findings.append(
                    f"  {column}:{line:<4} {'-':<9} {'':<14} SPLIT/JOIN\n"
                    f"      legacy   {leg_surfaces}\n"
                    f"      reviewed {rev_surfaces}"
                )

    if findings:
        print("\n".join(findings))
        print()

    compared = sum(tally[label] for label in ("AGREE", "AGREE~", "DIFFER", "NO-ANALYSIS"))
    print("summary")
    for label in ("AGREE", "AGREE~", "DIFFER", "NO-ANALYSIS"):
        if tally[label]:
            pct = f"{100 * tally[label] / compared:5.1f}%" if compared else "    -"
            print(f"  {label:<14}{tally[label]:>6}{pct:>9}")
    if tally["SPLIT/JOIN"]:
        print(f"  {'SPLIT/JOIN':<14}{tally['SPLIT/JOIN']:>6}    (token-boundary blocks, not tokens)")

    # Coverage matters: a high agreement rate over a small slice of the tablet
    # says nothing about the rest of it.
    pct = f"{100 * compared / scoped_tokens:.1f}%" if scoped_tokens else "-"
    print(f"\ncoverage      {compared} of {scoped_tokens} reviewed tokens in scope ({pct})")
    if absent_tokens:
        print(
            f"  {absent_tokens:>5} on {tally['lines-absent-from-legacy']} line(s) the legacy file"
            " does not cover -- it reviews only part of this tablet"
        )
    if uncomparable_tokens:
        print(f"  {uncomparable_tokens:>5} inside token-boundary mismatches, not comparable")
    if filtered_tokens:
        print(f"  {filtered_tokens:>5} excluded by --seeded-only")
    print("\nAGREE is corroboration, not proof. Adjudicate every DIFFER against DULAT and EUPT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
