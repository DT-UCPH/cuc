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
    REJECTED-AUTO
                comparison with the exact historical automatic basis proves
                that a reviewer who began from it removed one or more options;
                retain one only when an independent source supports it
    REJECTED-AUTO~
                the same relation once homonym tags are ignored
    CURRENT-EXTRA
                the current file has extra alternatives, but this comparison
                does not prove that the legacy reviewer ever saw them
    DIFFER      a real disagreement -- adjudicate it, do not assume either side
    SPLIT/JOIN  the two tokenizations disagree about word boundaries here

AGREE is corroboration, not proof: the legacy reviewer and the parser can be
wrong together. DIFFER and a historically proved REJECTED-AUTO are the
highest-value signals in the file. Ksenia, Elijah, and Alex reviewed automatic-
parser output, so an option demonstrably present in their basis and absent from
their review is an explicit rejection, not mere source silence. Tania worked
from a blank slate; her omissions are ordinary silence and cannot receive this
verdict.

Usage:
    legacy_align.py 1.14                      # whole tablet, disagreements only
    legacy_align.py 1.14 --columns IV,V,VI    # scope to the columns under review
    legacy_align.py 1.14 --all                # include agreements
    legacy_align.py 1.14 --legacy path.txt    # explicit legacy file
    legacy_align.py 2.14 \
      --legacy-ref origin/Elijahs_Tagging \
      --legacy-ref-path 'morphemes_files/KTU 2.14.csv' --legacy-csv
                                                # branch-resident review
    legacy_align.py 2.14 --automatic-basis-ref 6b1017f \
      --automatic-basis-path 'auto_parsing/0.2.6/KTU 2.14.tsv'
                                                # recover alternatives deleted
                                                # from the historical auto basis

See ../SKILL.md.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import io
import re
import subprocess
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


def has_homonym(analysis: str) -> bool:
    return HOMONYM_RE.search(analysis) is not None


def split_variants(analysis: str, *, packed_variants: bool) -> set[str]:
    values = analysis.split(";") if packed_variants else [analysis]
    normalized = {normalize(value) for value in values}
    return {value for value in normalized if value}


def load_rows(
    rows,
    idx: dict[str, int],
    *,
    source: str,
    packed_variants: bool = False,
    force_seeded: bool = False,
    delimiter: str = "\t",
):
    """Return {(column, line): [(id, surface, {analyses}, seeded)]} in file order."""
    blocks: dict[tuple[str, str], list] = defaultdict(list)
    reader = csv.reader(rows, delimiter=delimiter)
    next(reader, None)
    key = None
    by_id: dict[str, list] = {}
    last_entry = None
    for row in reader:
        if not row:
            continue
        marker = HEADER_RE.match(row[0])
        if marker:
            key = (marker.group(2) or "-", marker.group(3))
            by_id = {}
            last_entry = None
            continue
        if key is None:
            continue

        # Some expert CSVs put another analysis on a continuation row with a
        # blank id and surface. Keep it as an alternative for the preceding
        # token instead of silently losing an independent reading.
        if not row[0].strip():
            if last_entry is not None:
                pos = idx["analysis"]
                analysis = row[pos].strip() if len(row) > pos else ""
                last_entry[2].update(
                    split_variants(analysis, packed_variants=packed_variants)
                )
            continue
        if not row[0].strip().isdigit():
            continue

        def get(name: str) -> str:
            pos = idx[name]
            return row[pos].strip() if len(row) > pos else ""

        tid, surface = get("id"), get("surface")
        analyses = split_variants(get("analysis"), packed_variants=packed_variants)
        comment = get("comment")
        if tid in by_id:
            # Alternative row for a token already seen on this line.
            by_id[tid][2].update(analyses)
            last_entry = by_id[tid]
            continue
        entry = [tid, surface, analyses, force_seeded or SEED_MARK in comment]
        by_id[tid] = entry
        blocks[key].append(entry)
        last_entry = entry
    if not blocks:
        raise SystemExit(
            f"{source} has no '# KTU <tablet> <col>:<line>' markers, so it cannot be\n"
            "aligned by line reference. Files under reviewed/orig/ are bare id dumps\n"
            "without markers -- use a marked legacy file, or pass --legacy explicitly."
        )
    return blocks


def load(
    path: Path,
    idx: dict[str, int],
    *,
    packed_variants: bool = False,
    force_seeded: bool = False,
    delimiter: str = "\t",
):
    with path.open(encoding="utf-8") as fh:
        return load_rows(
            fh,
            idx,
            source=str(path),
            packed_variants=packed_variants,
            force_seeded=force_seeded,
            delimiter=delimiter,
        )


def load_git_review(
    ref: str,
    path: str,
    idx: dict[str, int],
    *,
    delimiter: str = "\t",
):
    source = f"{ref}:{path}"
    proc = subprocess.run(
        ["git", "show", source],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise SystemExit(f"cannot read branch review {source}:\n{proc.stderr.strip()}")
    return load_rows(
        io.StringIO(proc.stdout),
        idx,
        source=source,
        delimiter=delimiter,
    )


def load_automatic_basis(ref: str, tablet: str, path: str | None = None):
    path = path or f"auto_parsing/KTU {tablet}.tsv"
    source = f"{ref}:{path}"
    proc = subprocess.run(
        ["git", "show", source],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise SystemExit(
            f"cannot read historical automatic basis {source}:\n{proc.stderr.strip()}"
        )
    return load_rows(
        io.StringIO(proc.stdout),
        LEGACY_IDX,
        source=source,
        packed_variants=True,
        force_seeded=True,
    )


def verdict(
    left: set[str], right: set[str], *, proven_automatic_basis: bool = False
) -> str:
    """Compare legacy (left) and current (right) alternative sets.

    A proper subset is materially different from generic disagreement, but it
    is an explicit rejection only when ``right`` is the exact historical
    automatic basis the reviewer received. A current SEEDED marker alone does
    not establish that provenance; this matters especially for Tania's blank-
    slate review.
    """
    left = {a for a in left if a}
    right = {a for a in right if a}
    if not left or not right:
        return "NO-ANALYSIS"
    if left == right:
        return "AGREE"
    # Test exact set containment before broadening away homonym tags.  Otherwise
    # {l(I)} versus {l(I), l(II), l(III)} collapses to {l} == {l} and hides two
    # alternatives the reviewer explicitly removed.
    if left < right:
        return "REJECTED-AUTO" if proven_automatic_basis else "CURRENT-EXTRA"
    left_broad = {strip_homonyms(a) for a in left}
    right_broad = {strip_homonyms(a) for a in right}
    if left_broad == right_broad:
        return "AGREE~"
    # Broad containment is evidence of deletion only when the legacy side was
    # genuinely less specific (e.g. spr/).  If it explicitly says mlk(I)/ and
    # automatic has mlk(II)/, erasing both homonyms must not turn a lexical
    # disagreement into a subset relation.
    if left_broad < right_broad and all(not has_homonym(a) for a in left):
        return "REJECTED-AUTO~" if proven_automatic_basis else "CURRENT-EXTRA~"
    return "DIFFER"


def rejected_options(left: set[str], right: set[str], result: str) -> set[str]:
    """Return current alternatives absent from the legacy review."""
    if result in {"REJECTED-AUTO", "CURRENT-EXTRA"}:
        return {a for a in right if a and a not in left}
    if result in {"REJECTED-AUTO~", "CURRENT-EXTRA~"}:
        left_broad = {strip_homonyms(a) for a in left if a}
        return {a for a in right if a and strip_homonyms(a) not in left_broad}
    return set()


def fmt(analyses: set[str]) -> str:
    return " | ".join(sorted(a for a in analyses if a)) or "(none)"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("tablet", help="tablet number, e.g. 1.14")
    ap.add_argument("--columns", help="comma-separated column filter, e.g. IV,V,VI")
    source_group = ap.add_mutually_exclusive_group()
    source_group.add_argument("--legacy", help="explicit legacy file path")
    source_group.add_argument(
        "--legacy-ref", help="git ref containing a branch-resident expert review"
    )
    source_group.add_argument(
        "--current-as-review",
        action="store_true",
        help=(
            "compare the current reviewed TSV as an auto-based human review; "
            "requires --automatic-basis-ref and established provenance"
        ),
    )
    ap.add_argument(
        "--legacy-ref-path",
        help="repository path to the review used with --legacy-ref",
    )
    ap.add_argument(
        "--legacy-csv",
        action="store_true",
        help="read the explicit or branch-resident legacy review as CSV",
    )
    ap.add_argument(
        "--legacy-reviewed-layout",
        action="store_true",
        help="legacy source includes the reviewed TSV sign-span column",
    )
    ap.add_argument(
        "--automatic-basis-ref",
        help=(
            "compare with auto_parsing/KTU <tablet>.tsv at this git ref, "
            "recovering historical automatic alternatives the reviewer deleted"
        ),
    )
    ap.add_argument(
        "--automatic-basis-path",
        help=(
            "repository path of the exact automatic basis at that ref; defaults "
            "to unversioned auto_parsing/KTU <tablet>.tsv"
        ),
    )
    ap.add_argument("--all", action="store_true", help="list agreements too")
    ap.add_argument("--seeded-only", action="store_true", help="only rows still marked SEEDED")
    args = ap.parse_args()

    reviewed_path = ROOT / "reviewed" / f"KTU {args.tablet}.tsv"
    if not reviewed_path.exists():
        raise SystemExit(f"no reviewed TSV: {reviewed_path}")

    if args.current_as_review and not args.automatic_basis_ref:
        raise SystemExit("--current-as-review requires --automatic-basis-ref")
    if args.automatic_basis_path and not args.automatic_basis_ref:
        raise SystemExit("--automatic-basis-path requires --automatic-basis-ref")

    legacy_idx = REVIEWED_IDX if args.legacy_reviewed_layout else LEGACY_IDX
    legacy_delimiter = "," if args.legacy_csv else "\t"
    if args.current_as_review:
        legacy_path = reviewed_path
        legacy_label = str(reviewed_path.relative_to(ROOT))
        legacy = load(reviewed_path, REVIEWED_IDX)
    elif args.legacy_ref:
        if not args.legacy_ref_path:
            raise SystemExit("--legacy-ref requires --legacy-ref-path")
        legacy_path = None
        legacy_label = f"{args.legacy_ref}:{args.legacy_ref_path}"
        legacy = load_git_review(
            args.legacy_ref,
            args.legacy_ref_path,
            legacy_idx,
            delimiter=legacy_delimiter,
        )
    elif args.legacy_ref_path:
        raise SystemExit("--legacy-ref-path requires --legacy-ref")
    elif args.legacy:
        legacy_path = Path(args.legacy)
        legacy_label = str(legacy_path)
        legacy = load(
            legacy_path,
            legacy_idx,
            delimiter=legacy_delimiter,
        )
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
        legacy_label = str(legacy_path.relative_to(ROOT))
        legacy = load(legacy_path, LEGACY_IDX)

    wanted = {c.strip().upper() for c in args.columns.split(",")} if args.columns else None

    if args.automatic_basis_ref:
        reviewed = load_automatic_basis(
            args.automatic_basis_ref,
            args.tablet,
            args.automatic_basis_path,
        )
        basis_path = args.automatic_basis_path or f"auto_parsing/KTU {args.tablet}.tsv"
        reviewed_label = f"{args.automatic_basis_ref}:{basis_path}"
        right_name = "automatic"
    else:
        reviewed = load(reviewed_path, REVIEWED_IDX)
        reviewed_label = str(reviewed_path.relative_to(ROOT))
        right_name = "reviewed"
    print(f"{right_name + ':':<10}{reviewed_label}")
    print(f"legacy:   {legacy_label}")
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
                    result = verdict(
                        leg[2],
                        rev[2],
                        proven_automatic_basis=bool(args.automatic_basis_ref),
                    )
                    tally[result] += 1
                    if result in ("AGREE", "AGREE~") and not args.all:
                        continue
                    seed = " [SEEDED]" if rev[3] else ""
                    finding = (
                        f"  {column}:{line:<4} {rev[0]:<9} {rev[1]:<14} {result:<11}{seed}\n"
                        f"      legacy   {fmt(leg[2])}\n"
                        f"      {right_name:<10}{fmt(rev[2])}"
                    )
                    rejected = rejected_options(leg[2], rev[2], result)
                    if rejected:
                        finding += f"\n      removed   {fmt(rejected)}"
                    findings.append(finding)
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
                    f"      {right_name:<10}{rev_surfaces}"
                )

    if findings:
        print("\n".join(findings))
        print()

    comparison_labels = (
        "AGREE",
        "AGREE~",
        "REJECTED-AUTO",
        "REJECTED-AUTO~",
        "CURRENT-EXTRA",
        "CURRENT-EXTRA~",
        "DIFFER",
        "NO-ANALYSIS",
    )
    compared = sum(tally[label] for label in comparison_labels)
    print("summary")
    for label in comparison_labels:
        if tally[label]:
            pct = f"{100 * tally[label] / compared:5.1f}%" if compared else "    -"
            print(f"  {label:<14}{tally[label]:>6}{pct:>9}")
    if tally["SPLIT/JOIN"]:
        print(
            f"  {'SPLIT/JOIN':<14}{tally['SPLIT/JOIN']:>6}    "
            "(token-boundary blocks, not tokens)"
        )

    # Coverage matters: a high agreement rate over a small slice of the tablet
    # says nothing about the rest of it.
    pct = f"{100 * compared / scoped_tokens:.1f}%" if scoped_tokens else "-"
    print(f"\ncoverage      {compared} of {scoped_tokens} {right_name} tokens in scope ({pct})")
    if absent_tokens:
        print(
            f"  {absent_tokens:>5} on {tally['lines-absent-from-legacy']} line(s) the legacy file"
            " does not cover -- it reviews only part of this tablet"
        )
    if uncomparable_tokens:
        print(f"  {uncomparable_tokens:>5} inside token-boundary mismatches, not comparable")
    if filtered_tokens:
        print(f"  {filtered_tokens:>5} excluded by --seeded-only")
    guidance = (
        "\nAGREE is corroboration, not proof. Adjudicate every DIFFER against DULAT "
        "and EUPT."
    )
    if args.automatic_basis_ref:
        guidance += (
            " REJECTED-AUTO is an explicit reviewer rejection: drop the removed "
            "option unless an independent source supports it."
        )
    else:
        guidance += (
            " CURRENT-EXTRA records ordinary source silence; it does not prove that "
            "the legacy reviewer rejected the extra option."
        )
    print(guidance)
    return 0


if __name__ == "__main__":
    sys.exit(main())
