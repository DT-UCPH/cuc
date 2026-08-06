#!/usr/bin/env python3
"""What every source says about one line, in a single call.

This answers the first question of a review pass: before deciding a token, see
what DULAT cites here, who reads it differently, how each translation renders
it, what EUPT analyses, and how Burns classifies it.

Sources, all resolved without any machine-specific path (see sources.py):

  dulat_search.sqlite   dulat_reverse_refs — which DULAT entries are cited at a
                        given line, with the reference-specific translation
  dulat_cache.sqlite    article text, mined for the '(… diff. …)' notes that
                        record a dissenting reading FOR THAT PLACE ONLY
  modules_cache.sqlite  15 modules. Line-level: EUPT vocalisation, translation
                        and commentary, plus the CUC text. Tablet-level: UNP,
                        TCS, Smith, Coogan, ANET, DeMoor, Gordon — whole
                        documents, so use --grep to find the passage inside one.
  Burns workbooks       headword, root, and the DN/PN/GN/cultic classification;
                        licensed CC BY-NC-ND 2.5, so cite rather than copy

DULAT and Tropper outrank the rest; EUPT is preliminary draft material and Burns
triangulates. Keep the losing readings as alternative rows rather than deleting
them — see ../references/evidence-sources.md.

    sources_lookup.py --ktu 1.14:IV:35
    sources_lookup.py --ktu 1.5:I:14 --modules UNP,TCS --grep tear
    sources_lookup.py --list

References are stored in CAT notation ('CAT 1.14 IV:35'); KTU input is
translated automatically. See ../SKILL.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402

LINE_LEVEL = ("EUPT_vocalisation", "EUPT_translation", "EUPT_commentary", "CUC")

# DULAT cites attestations as '1.14 IV 38' inside the article text, and records a
# dissenting reading for that one place as '(… diff. <author> <ref>: "…")'.
DIFF_RE = re.compile(r"\(([^()]{0,400}?\bdiff\.[^()]{0,400}?)\)")
# Burns references: 'I.37, 43; III.32, 47' — column-qualified, or bare lines.
BURNS_COL = re.compile(r"^([IVX]+)\.(.*)$")


def to_cat(ktu: str) -> str:
    m = re.match(r"(?:KTU\s*)?(\d+\.\d+)(?::([IVX]+))?(?::(\d+))?$", ktu.strip())
    if not m:
        raise SystemExit("reference form: 1.14 | 1.14:IV | 1.14:IV:35")
    tab, col, line = m.group(1), m.group(2), m.group(3)
    out = "CAT " + tab
    if col:
        out += " " + col
        if line:
            out += ":" + line
    return out


def wrap(text, indent="      ", width=96):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent) if text else indent + "(empty)"


def show_dulat(ref: str, args):
    db = sources.locate("dulat_search", args.dulat_search, required=False)
    if db is None:
        print("DULAT citations: (dulat_search database not located; set CUC_DULAT_SEARCH_DB)")
        return
    con = sources.connect_ro(db)
    rows = list(con.execute(
        "select entry_id, payload from dulat_reverse_refs where norm_ref=? order by entry_id",
        (ref,)))
    print("DULAT entries cited at %s: %d" % (ref, len(rows)))
    for entry_id, payload in rows[: args.limit]:
        try:
            d = json.loads(payload)
        except Exception:
            continue
        label = re.sub(r"<[^>]+>", "", d.get("label") or "").strip()
        senses = d.get("sense_labels") or []
        print("  entry %-6s %s" % (entry_id, label or "(no label)"))
        if senses:
            print(wrap(senses[0][:400]))
    con.close()


def dulat_citation(ref: str) -> str:
    """'CAT 1.14 IV:35' -> '1.14 IV 35', the form DULAT uses inside its articles."""
    return ref.replace("CAT ", "").replace(":", " ")


def show_dulat_diff(ref: str, args):
    """Dissenting readings DULAT records for *this* attestation only."""
    db = sources.locate("dulat", args.dulat, required=False, quiet=True)
    if db is None:
        return
    cite = dulat_citation(ref)
    # '1.6 VI 4' must not match '1.6 VI 40'/'45'; anchor on a non-digit boundary.
    cite_re = re.compile(re.escape(cite) + r"(?!\d)")
    con = sources.connect_ro(db)
    found = []
    for entry_id, lemma, text in con.execute(
            "select entry_id, lemma, text from entries where text like ?", ("%" + cite + "%",)):
        plain = re.sub(r"<[^>]+>", "", text or "")
        for m in DIFF_RE.finditer(plain):
            # The note belongs to the nearest citation before it, so only report
            # it when ours is that citation.
            before = plain[max(0, m.start() - 260):m.start()]
            hits = list(cite_re.finditer(before))
            if not hits:
                continue
            # No other line citation may intervene between ours and the note.
            tail = before[hits[-1].end():]
            if re.search(r"\d\.\d+\s+[IVX]*\s*\d", tail):
                continue
            found.append((entry_id, lemma, re.sub(r"\s+", " ", m.group(1)).strip()))
    con.close()
    if not found:
        return
    print("\nDULAT 'diff.' — dissenting readings recorded for %s specifically" % ref)
    for entry_id, lemma, note in found[: args.limit]:
        print("  %-6s %-10s %s" % (entry_id, lemma, note[:300]))
    print("  (These attach to this attestation only — never generalise one to the lemma.)")


def burns_index(root_dir: Path):
    """{(tablet, column, line): [row]} over the workbook CSVs."""
    idx = {}
    for csv_path in sorted(root_dir.glob("*/*.csv")):
        workbook = csv_path.parent.name
        with csv_path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                tablet = (row.get("ktu") or "").strip()
                refs = (row.get("references") or "").strip()
                if not tablet or not refs or tablet.lower().startswith("not attested"):
                    continue
                for chunk in refs.split(";"):
                    chunk = chunk.strip()
                    if not chunk:
                        continue
                    m = BURNS_COL.match(chunk)
                    column, rest = (m.group(1), m.group(2)) if m else ("", chunk)
                    for line in re.findall(r"\d+", rest):
                        idx.setdefault((tablet, column, line), []).append((workbook, row))
    return idx


def show_burns(ktu_ref: str, args):
    root_dir = sources.locate("burns", args.burns, required=False, quiet=True)
    if root_dir is None:
        return
    if (root_dir / "output").is_dir():
        root_dir = root_dir / "output"
    m = re.match(r"(\d+\.\d+)(?::([IVX]+))?(?::(\d+))?$", ktu_ref.strip())
    tablet, column, line = m.group(1), m.group(2) or "", m.group(3)
    if not line:
        return
    hits = burns_index(root_dir).get((tablet, column, line), [])
    print("\nBurns (2003) cultic-vocabulary workbooks at KTU %s: %d row(s)" % (ktu_ref, len(hits)))
    if not hits:
        print("  (not treated here — Burns covers cultic vocabulary and onomastica, not every token)")
        return
    seen = set()
    for workbook, row in hits[: args.limit]:
        key = (workbook, row.get("headword"), row.get("root"))
        if key in seen:
            continue                       # find-spot rows repeat the headword
        seen.add(key)
        category = re.sub(r"^\d+\s+Workbook\s+[IVX]+\s*-\s*", "", workbook)
        print("  %-26s %-14s %s" % (category, row.get("headword") or "",
                                    ("root " + row["root"]) if row.get("root") else ""))
        if row.get("comments"):
            print(wrap(row["comments"][:400], indent="        "))
    print("  Triangulation only, and below Tropper and DULAT. Burns is licensed"
          " CC BY-NC-ND 2.5 — cite, do not bulk-copy.")


def show_word_morphology(data_json):
    """Per-token morphology from data_json -> words[].

    Reading only content_text throws this away, and it is the most decisive
    thing the modules hold: EUPT states stem, conjugation, person, gender,
    number and lemma per token, e.g. 'N-PKL 3.m.Du.' for yinnagiḥāni.
    """
    if not data_json:
        return
    try:
        words = (json.loads(data_json) or {}).get("words") or []
    except Exception:
        return
    if not words:
        return
    print("      %-20s %-24s %-10s %s" % ("form", "morph", "lemma", "hom."))
    for w in words:
        print("      %-20s %-24s %-10s %s" % (
            (w.get("form") or "")[:20], (w.get("morph") or "")[:24],
            (w.get("lemma") or "")[:10], w.get("homonym") or ""))
    print("      (EUPT tags: GN = Gottesname = our DN; PKL/PKK = long/short prefix"
          " conjugation; SK = suffix conjugation. Full table in dulat-recipes.md.)")


def show_modules(ref: str, tablet_ref: str, args):
    db = sources.locate("modules", args.modules_db, required=False)
    if db is None:
        print("\nModules: (modules database not located; set CUC_MODULES_DB)")
        return
    con = sources.connect_ro(db)
    wanted = {m.strip() for m in args.modules.split(",")} if args.modules else None

    print("\nLine-level modules at %s" % ref)
    got = False
    for mod in LINE_LEVEL:
        if wanted and mod not in wanted:
            continue
        for txt, data in con.execute(
            "select content_text, data_json from module_records "
            "where module_id=? and ref_norm=?", (mod, ref)):
            got = True
            print("  [%s]" % mod)
            print(wrap(txt))
            show_word_morphology(data)
    if not got:
        print("  (nothing at this exact line)")

    print("\nTablet-level modules at %s  (whole documents)" % tablet_ref)
    rows = list(con.execute(
        "select module_id, content_text from module_records "
        "where ref_norm=? and module_id not in (%s) order by module_id"
        % ",".join("?" * len(LINE_LEVEL)),
        (tablet_ref,) + LINE_LEVEL))
    if not rows:
        print("  (none)")
    for mod, txt in rows:
        if wanted and mod not in wanted:
            continue
        if args.grep:
            hits = [m for m in re.finditer(re.escape(args.grep), txt or "", re.I)]
            if not hits:
                print("  [%s] %d chars — no match for %r" % (mod, len(txt or ""), args.grep))
                continue
            print("  [%s] %d match(es) for %r" % (mod, len(hits), args.grep))
            for h in hits[:3]:
                print(wrap("…" + (txt[max(0, h.start() - 120):h.end() + 120]) + "…"))
        else:
            print("  [%s] %d chars — pass --grep WORD to search inside"
                  % (mod, len(txt or "")))
    con.close()


def list_modules(args):
    db = sources.locate("modules", args.modules_db)
    con = sources.connect_ro(db)
    print("%-22s %-12s %-6s %s" % ("module", "type", "lang", "records / ref granularity"))
    for mid, title, typ, lang in con.execute(
            "select id, title, type, language from modules order by id"):
        n, sample = con.execute(
            "select count(*), min(ref_norm) from module_records where module_id=?",
            (mid,)).fetchone()
        gran = "line" if mid in LINE_LEVEL else "tablet"
        print("%-22s %-12s %-6s %5d  %-6s %s" % (mid, typ, lang, n or 0, gran, sample or ""))
    con.close()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ktu", help="1.14:IV:35 (or 1.14:IV, or 1.14)")
    ap.add_argument("--modules", help="comma-separated module filter, e.g. UNP,TCS")
    ap.add_argument("--grep", help="search inside tablet-level documents")
    ap.add_argument("--list", action="store_true", help="list available modules")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--dulat", help="override the structured DULAT database")
    ap.add_argument("--burns", help="override the Burns workbooks directory")
    ap.add_argument("--dulat-search", help="override the dulat_search database")
    ap.add_argument("--modules-db", help="override the modules database")
    args = ap.parse_args()

    if args.list:
        return list_modules(args)
    if not args.ktu:
        ap.print_help()
        return 1

    ref = to_cat(args.ktu)
    tablet_ref = " ".join(ref.split()[:2])
    show_dulat(ref, args)
    show_dulat_diff(ref, args)
    show_modules(ref, tablet_ref, args)
    show_burns(args.ktu, args)
    print("\nCite what you read, and keep translations' disagreements rather than "
          "collapsing them (see ../references/comment-conventions.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
