#!/usr/bin/env python3
"""Audit onomastic (DN/PN/GN/TN) POS-vs-gloss consistency in CUC TSV files.

The detectors are self-calibrating: for each DULAT lexeme+homonym the script
cross-tabulates POS class against gloss and flags the minority cells. It hard-codes
no list of "name-looking" glosses, so it works on any tablet.

Every finding is a candidate, not a verdict. Confirm against DULAT before editing.
See ../SKILL.md.
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ONOMASTIC_TAGS = ("DN", "PN", "GN", "TN", "MN")

# Reviewed layout carries an extra "sign span" column that automatic output lacks.
REVIEWED_COLUMNS = ["id", "surface", "sign_span", "analysis", "dulat", "pos", "gloss", "comment"]
AUTO_COLUMNS = ["id", "surface", "analysis", "dulat", "pos", "gloss", "comment"]

HEADER_RE = re.compile(r"^# KTU (\S+)(?: ([IVX]+):| )(\d+)")
HOM_RE = re.compile(r"^(.*?)\s*\(([IVX]+)\)\s*$")


def repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "reviewed").is_dir() and (candidate / "agent").is_dir():
            return candidate
    raise SystemExit("Could not locate repo root (needs reviewed/ and agent/ siblings)")


def dulat_db(root: Path) -> Path:
    sys.path.insert(0, str(root / "agent"))
    try:
        from project_paths import get_project_paths  # type: ignore

        return get_project_paths().default_dulat_db()
    except Exception:
        return root / "agent" / "local_sources" / "dulat_cache.sqlite"


def load_rows(path: Path):
    """Yield dict rows, auto-detecting the reviewed sign-span column."""
    lines = path.read_text(encoding="utf-8").splitlines()
    columns = None
    for raw in lines:
        parts = raw.split("\t")
        if parts and parts[0].strip().lower() == "id":
            columns = (
                REVIEWED_COLUMNS
                if len(parts) >= 3 and parts[2].strip().lower() == "sign span"
                else AUTO_COLUMNS
            )
            break
    if columns is None:
        return
    loc = ""
    for raw in lines:
        if raw.startswith("#"):
            m = HEADER_RE.match(raw)
            if m:
                col = f" {m.group(2)}" if m.group(2) else ""
                loc = f"KTU {m.group(1)}{col}:{m.group(3)}"
            continue
        parts = raw.split("\t")
        if not parts or not parts[0].strip().isdigit():
            continue
        row = {c: (parts[i].strip() if i < len(parts) else "") for i, c in enumerate(columns)}
        row["loc"] = loc
        row["file"] = path.name
        yield row


def pos_class(pos: str) -> str | None:
    """Onomastic tag, 'common', or None for unresolved rows."""
    pos = (pos or "").strip()
    for tag in ONOMASTIC_TAGS:
        if pos.startswith(tag):
            return "GN" if tag in ("GN", "TN") else tag
    return None if pos in ("", "?") else "common"


def split_dulat(token: str) -> tuple[str, str]:
    token = (token or "").strip()
    m = HOM_RE.match(token)
    return (m.group(1), m.group(2)) if m else (token, "")


def normalise(text: str) -> str:
    return (text or "").strip().lower().translate(
        str.maketrans({"ʿ": "ʕ", "ˤ": "ʕ", "ʾ": "ʔ", "ả": "a", "ỉ": "i", "ủ": "u"})
    )


def load_dulat_entries(db: Path) -> dict[tuple[str, str], str]:
    """(lemma, homonym) -> DULAT pos string."""
    if not db.exists():
        return {}
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return {
        (normalise(r["lemma_lower"] or r["lemma"] or ""), r["homonym"] or ""): (r["pos"] or "")
        for r in con.execute("select lemma, lemma_lower, homonym, pos from entries")
    }


def load_overrides(path: Path) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    if not path.exists():
        return keys
    for row in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"):
        lemma, hom = split_dulat(row.get("dulat", ""))
        keys.add((normalise(lemma), hom))
    return keys


_GLOSS_NOISE_RE = re.compile(r"^\s*\d+\)\s*|\s*[a-z]\)\s*")


def gloss_core(gloss: str) -> set[str]:
    """Content words of a gloss, ignoring DULAT sense-path numbering."""
    text = _GLOSS_NOISE_RE.sub(" ", (gloss or "").lower())
    return {w for w in re.split(r"[^\w-￿]+", text) if len(w) > 2}


def glosses_are_nested(a: str, b: str) -> bool:
    """True when one gloss merely elaborates the other (same head sense).

    'dust' vs '1) dust b) meton' and 'to protect' vs 'to protect, guard' are the
    same decision at different specificity, not a disagreement worth reporting.
    """
    ca, cb = gloss_core(a), gloss_core(b)
    if not ca or not cb:
        return True
    return ca <= cb or cb <= ca


def fmt(r: dict) -> str:
    return (
        f"{r['id']} {r['loc']:16s} {r['surface']:10s} {r['dulat']:13s} "
        f"POS={r['pos']:28s} gloss={r['gloss'][:34]!r}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="+", help="TSV files or directories")
    ap.add_argument(
        "--min-majority",
        type=int,
        default=3,
        help="minimum sibling rows before a minority cell is reported (default 3)",
    )
    ap.add_argument("--only", choices=["pos-minority", "gloss-minority", "allowlist-gap", "gloss-drift"])
    args = ap.parse_args()

    root = repo_root(Path.cwd().resolve())
    entries = load_dulat_entries(dulat_db(root))
    overrides = load_overrides(root / "agent" / "data_sources" / "onomastic_gloss_overrides.tsv")

    paths: list[Path] = []
    for target in args.targets:
        p = Path(target)
        if not p.is_absolute():
            p = root / target
        paths.extend(sorted(p.glob("*.tsv")) if p.is_dir() else [p])

    rows = [r for p in paths if p.exists() for r in load_rows(p)]
    if not rows:
        print("No rows found.", file=sys.stderr)
        return 1

    # lexeme -> POS class counts, and (lexeme, POS class) -> gloss counts
    pos_by_lex: dict[tuple[str, str], Counter] = defaultdict(Counter)
    gloss_by_cell: dict[tuple[str, str, str], Counter] = defaultdict(Counter)
    for r in rows:
        cls = pos_class(r["pos"])
        lemma, hom = split_dulat(r["dulat"])
        if cls is None or not lemma:
            continue
        key = (normalise(lemma), hom)
        pos_by_lex[key][cls] += 1
        if r["gloss"] and r["gloss"] != "?":
            gloss_by_cell[(*key, cls)][r["gloss"]] += 1

    findings: dict[str, list[str]] = defaultdict(list)

    for r in rows:
        cls = pos_class(r["pos"])
        lemma, hom = split_dulat(r["dulat"])
        if cls is None or not lemma:
            continue
        key = (normalise(lemma), hom)

        # 1. This row's POS class is a minority for its lexeme.
        counts = pos_by_lex[key]
        if len(counts) > 1 and sum(counts.values()) >= args.min_majority:
            top, top_n = counts.most_common(1)[0]
            if cls != top and counts[cls] * 4 <= top_n:
                findings["pos-minority"].append(
                    f"{fmt(r)}  — {counts[cls]}x {cls} vs {top_n}x {top} for {r['dulat']}"
                )

        # 2. This row's gloss is a minority within its own lexeme+POS cell, and
        #    differs from the majority in substance rather than in specificity.
        gcounts = gloss_by_cell.get((*key, cls), Counter())
        if len(gcounts) > 1 and sum(gcounts.values()) >= args.min_majority and r["gloss"]:
            top_g, top_gn = gcounts.most_common(1)[0]
            if (
                r["gloss"] != top_g
                and gcounts[r["gloss"]] * 4 <= top_gn
                and not glosses_are_nested(r["gloss"], top_g)
            ):
                findings["gloss-minority"].append(
                    f"{fmt(r)}  — {gcounts[r['gloss']]}x vs {top_gn}x {top_g!r}"
                )

        # 3. Onomastic POS the linter's allowlist will reject.
        if cls != "common":
            entry_pos = entries.get(key)
            if (
                entry_pos is not None
                and not any(t.lower() in entry_pos.lower() for t in ONOMASTIC_TAGS)
                and key not in overrides
            ):
                findings["allowlist-gap"].append(
                    f"{fmt(r)}  — DULAT pos={entry_pos!r}; add '{r['dulat']}' to "
                    f"onomastic_gloss_overrides.tsv (key MUST include the homonym)"
                )

    # 4. Whole-lexeme gloss drift, for a curation pass rather than a per-row fix.
    for (lemma, hom, cls), gcounts in sorted(gloss_by_cell.items()):
        if cls != "common" and len(gcounts) > 1:
            spread = " | ".join(f"{g!r}x{n}" for g, n in gcounts.most_common(5))
            findings["gloss-drift"].append(f"{lemma} ({hom}) [{cls}]: {spread}")

    total = 0
    for name in ("pos-minority", "gloss-minority", "allowlist-gap", "gloss-drift"):
        items = findings.get(name, [])
        if (args.only and args.only != name) or not items:
            continue
        # De-duplicate allowlist-gap by lexeme to keep the report short.
        if name == "allowlist-gap":
            seen, deduped = set(), []
            for line in items:
                k = line.split("DULAT pos=")[-1] + line.split()[3]
                if k not in seen:
                    seen.add(k)
                    deduped.append(line)
            items = deduped
        print(f"\n=== {name} ({len(items)}) ===")
        for line in items:
            print("  " + line)
        total += len(items)

    print(f"\nTotal candidates: {total}  (rows scanned: {len(rows)})")
    print("Candidates are not verdicts — confirm each against DULAT before editing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
