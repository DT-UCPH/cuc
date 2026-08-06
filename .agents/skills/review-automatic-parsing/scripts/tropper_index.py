#!/usr/bin/env python3
"""Build and query a validated index of Tropper, Ugaritische Grammatik (2012).

The source is an OCR of the printed grammar. Its reliability is uneven and
tracks how numeric the content is: the KTU passage register is almost pure
digits and validates at ~99% against our own corpus, while the root register is
nothing but diacritics and is the worst text in the book. This tool therefore
records a `verified` flag per row rather than presenting one uniform index, and
prints a quality report on every build so a re-OCR can be measured against the
last one.

Nothing here is hand-corrected. Repairs are rule-based and validated against
the corpus, so rebuilding after a better OCR run is always safe.

    tropper_index.py build                       # parse + validate -> sqlite
    tropper_index.py lookup --ktu 1.14:IV:35     # what does he say about this line
    tropper_index.py lookup --term Energikus     # subject register
    tropper_index.py lookup --root ʿrb           # root register (unverified)
    tropper_index.py lookup --page 497           # printed page -> PDF page

Source location is resolved by sources.py: --ocr, then $CUC_TROPPER_OCR, then a
ugaritic_ocr checkout found beside the repository. No path is hardcoded. See
../SKILL.md and ../references/tropper-conventions.md.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402

CORPUS_HDR = re.compile(r"^# KTU (\S+)(?: ([IVX]+):| )(\d+)")
# '1.14:III:8 255, 281' | '3.9:6f.  225, 451' | '39:11 69' (lost dot)
# | '1.6:II:19664.' (page number fused onto the line number)
KTU_ENTRY = re.compile(
    r"^\s*(\d{1,2})[.\s]?(\d{1,3})"      # tablet, dot sometimes lost to OCR
    r"(?::([IVX]+))?"                     # optional column
    r":(.*)$"                             # line spec + pages, parsed in code
)
MAX_PAGE = 1100          # printed pages run to ~1076; anything above is a fusion
KTU_TAIL = re.compile(r"^(\d{1,5})([-–.\d'f]*?)\s*([\d,\s]*)$")
SUBJECT_ENTRY = re.compile(r"^\s*([A-ZÄÖÜ][^\d]{3,60}?)\s+(\d{1,4})\s*$")
ROOT_ENTRY = re.compile(
    r"^\s*([√/]?)\s*⸢?([ʾʿbgdhwzḥḫṭyklmnspṣqrsštṯḏġẓ]{2,5})[\(₀-₉\)]*\s+[⸢(]?\s*(\d[\d,\s]*)"
)


ROOT = sources.ROOT


def resolve_source(explicit):
    """Return (ocr_txt, searchable_pdf | None)."""
    target = sources.locate("tropper", explicit)
    d = target.parent if target.is_file() else target
    if target.is_file() and target.suffix == ".txt":
        txt = target
    else:
        txts = sorted(d.glob("*.ocr.txt"))
        if not txts:
            raise SystemExit("no *.ocr.txt under %s" % d)
        txt = txts[0]
    return txt, next(iter(sorted(d.glob("*searchable*.pdf"))), None)


def index_db_path(ocr: Path) -> Path:
    return ocr.with_suffix(".index.sqlite")


connect_ro = sources.connect_ro


# --------------------------------------------------------------------------- corpus


def corpus_lines():
    """{tablet: {(column, line)}} from the newest auto_parsing version."""
    vers = sorted(
        (p for p in (ROOT / "auto_parsing").glob("*") if p.is_dir()),
        key=lambda p: [int(x) for x in re.findall(r"\d+", p.name)] or [0],
    )
    if not vers:
        return {}, None
    latest = vers[-1]
    out = defaultdict(set)
    for f in glob.glob(str(latest / "*.tsv")):
        with open(f, encoding="utf-8") as fh:
            for row in csv.reader(fh, delimiter="\t"):
                if not row:
                    continue
                m = CORPUS_HDR.match(row[0])
                if m:
                    out[m.group(1)].add((m.group(2) or "", m.group(3)))
    return out, latest.name


def dulat_roots():
    db = sources.locate("dulat", required=False, quiet=True)
    if db is None:
        return set()
    con = connect_ro(db)
    out = set()
    for (lemma,) in con.execute("select lemma from entries where lemma like '/%'"):
        stem = lemma.strip("/").replace("-", "").replace("*", "")
        out.add(stem.replace("\u0294", "\u02be").replace("\u0295", "\u02bf"))
    con.close()
    return out


# --------------------------------------------------------------------------- pages


def detect_page_offset(pdf: Path | None):
    """printed_page = pdf_page - offset. Probed, not assumed."""
    if pdf is None or not shutil.which("pdftotext"):
        return None
    votes = defaultdict(int)
    for probe in (150, 300, 450, 600, 750, 900):
        try:
            txt = subprocess.run(
                ["pdftotext", "-f", str(probe), "-l", str(probe), str(pdf), "-"],
                capture_output=True, text=True, timeout=60,
            ).stdout
        except Exception:
            continue
        for m in re.finditer(r"(?m)^\s*(\d{2,4})\s*$", txt):
            printed = int(m.group(1))
            if 0 < probe - printed < 60:
                votes[probe - printed] += 1
    return max(votes, key=votes.get) if votes else None


# --------------------------------------------------------------------------- regions


def dense_regions(flags, window=100, threshold=0.45):
    """Line ranges where index-shaped lines dominate — avoids TOC and body text."""
    spans, run = [], None
    for i in range(0, max(len(flags) - window, 1)):
        d = sum(flags[i:i + window]) / float(window)
        if d >= threshold:
            run = (run[0], i + window) if run else (i, i + window)
        elif run and i > run[1]:
            spans.append(run)
            run = None
    if run:
        spans.append(run)
    return [s for s in spans if s[1] - s[0] >= window]


# --------------------------------------------------------------------------- parse


def parse_ktu(lines, corpus):
    """Yield dicts for KTU register entries, repairing two OCR classes.

    Both repairs are validated against the corpus: a repair is only taken when
    it produces a line that actually exists. An unrepairable row is kept with
    verified=0 rather than dropped, so the quality report stays honest.
    """
    flags = [1 if KTU_ENTRY.match(x) else 0 for x in lines]
    rows, repaired_dot, repaired_fuse, unparsed = [], 0, 0, 0
    for lo, hi in dense_regions(flags):
        for raw in lines[lo:hi]:
            m = KTU_ENTRY.match(raw)
            if not m:
                continue
            head, tail, col, rem = m.groups()
            col = col or ""
            tablet = "%s.%s" % (head, tail)
            t = KTU_TAIL.match(rem.strip())
            if not t:
                unparsed += 1
                continue
            first, span, pages_txt = t.groups()
            lost_dot = "." not in raw[: m.end(2)]
            if lost_dot:
                repaired_dot += 1

            line_no = first
            page_list = [int(p) for p in re.findall(r"\d+", pages_txt)]
            known = corpus.get(tablet)

            # A page number fused onto the line number: '1.6:II:19664.' -> 19 / 664.
            if known and (col, line_no) not in known and len(first) > 2:
                for cut in (1, 2, 3):
                    cand, spill = first[:cut], first[cut:]
                    if spill and (col, cand) in known:
                        line_no, page_list = cand, [int(spill)] + page_list
                        repaired_fuse += 1
                        break

            # A range end fused onto the page: '1.14:IV:36-43380' -> 36-43, p.380.
            fixed = []
            for p in page_list:
                if p <= MAX_PAGE:
                    fixed.append(p)
                    continue
                s = str(p)
                for cut in (1, 2, 3):
                    head_n, tail_n = s[:cut], s[cut:]
                    if tail_n and 9 < int(tail_n) <= MAX_PAGE:
                        if span.endswith("-"):
                            span = span + head_n
                        fixed.append(int(tail_n))
                        repaired_fuse += 1
                        break
                else:
                    fixed.append(p)          # implausible and unrepairable: keep, flag below
            page_list = fixed

            # Tropper's page lists run ascending; anything else is an OCR artefact.
            suspect = int(any(b < a for a, b in zip(page_list, page_list[1:]))
                          or any(p > MAX_PAGE for p in page_list))

            rows.append(
                dict(tablet=tablet, column=col, line=line_no, span=(span or "").strip(),
                     pages=",".join(str(p) for p in page_list),
                     verified=int(bool(known) and (col, line_no) in known),
                     in_corpus=int(bool(known)), pages_suspect=suspect,
                     repaired=int(lost_dot or line_no != first), raw=raw.strip())
            )
    return rows, repaired_dot, repaired_fuse, unparsed


def parse_subjects(lines):
    flags = [1 if SUBJECT_ENTRY.match(x) else 0 for x in lines]
    rows = []
    for lo, hi in dense_regions(flags, window=60, threshold=0.4):
        for raw in lines[lo:hi]:
            m = SUBJECT_ENTRY.match(raw)
            if m:
                rows.append(dict(term=m.group(1).strip(), pages=m.group(2), raw=raw.strip()))
    return rows


def parse_roots(lines, dulat):
    flags = [1 if ROOT_ENTRY.match(x) else 0 for x in lines]
    rows, clean_marker = [], 0
    for lo, hi in dense_regions(flags, window=60, threshold=0.4):
        for raw in lines[lo:hi]:
            m = ROOT_ENTRY.match(raw)
            if not m:
                continue
            marker, root, pages = m.groups()
            if marker == "√":
                clean_marker += 1
            rows.append(
                dict(root=root, pages=",".join(re.findall(r"\d+", pages)),
                     in_dulat=int(root in dulat), marker_ok=int(marker == "√"),
                     raw=raw.strip())
            )
    return rows, clean_marker


# --------------------------------------------------------------------------- build

SCHEMA = """
create table meta (key text primary key, value text);
create table ktu (tablet text, column text, line text, span text, pages text,
                 verified int, in_corpus int, pages_suspect int, repaired int, raw text);
create table subjects (term text, pages text, raw text);
create table roots (root text, pages text, in_dulat int, marker_ok int, raw text);
create index ktu_ref on ktu (tablet, column, line);
create index subj_term on subjects (term);
create index root_r on roots (root);
"""


def build(args):
    ocr, pdf = resolve_source(args.ocr)
    text = ocr.read_text(encoding="utf-8")
    lines = text.split("\n")
    digest = hashlib.sha256(ocr.read_bytes()).hexdigest()[:16]

    corpus, corpus_ver = corpus_lines()
    dulat = dulat_roots()
    offset = detect_page_offset(pdf)

    ktu, rep_dot, rep_fuse, unparsed = parse_ktu(lines, corpus)
    subjects = parse_subjects(lines)
    roots, clean_marker = parse_roots(lines, dulat)

    out = Path(args.out) if args.out else index_db_path(ocr)
    if out.exists():
        out.unlink()
    con = sqlite3.connect(str(out))
    con.executescript(SCHEMA)
    con.executemany(
        "insert into ktu values (:tablet,:column,:line,:span,:pages,:verified,"
        ":in_corpus,:pages_suspect,:repaired,:raw)", ktu)
    con.executemany("insert into subjects values (:term,:pages,:raw)", subjects)
    con.executemany(
        "insert into roots values (:root,:pages,:in_dulat,:marker_ok,:raw)", roots)

    checkable = [r for r in ktu if r["in_corpus"]]
    verified = [r for r in checkable if r["verified"]]
    rate = 100.0 * len(verified) / max(len(checkable), 1)
    meta = {
        "built": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ocr_file": str(ocr), "ocr_sha256_16": digest,
        "ocr_bytes": str(len(text)),
        "searchable_pdf": str(pdf) if pdf else "",
        "page_offset": "" if offset is None else str(offset),
        "corpus_version": corpus_ver or "",
        "ktu_rows": str(len(ktu)), "ktu_checkable": str(len(checkable)),
        "ktu_verified": str(len(verified)), "ktu_verified_pct": "%.1f" % rate,
        "ktu_repaired_dot": str(rep_dot), "ktu_repaired_fused_page": str(rep_fuse),
        "ktu_unparsed": str(unparsed),
        "ktu_pages_suspect": str(sum(r["pages_suspect"] for r in ktu)),
        "subject_rows": str(len(subjects)),
        "root_rows": str(len(roots)),
        "root_marker_ok": str(clean_marker),
        "root_in_dulat": str(sum(r["in_dulat"] for r in roots)),
    }
    con.executemany("insert into meta values (?,?)", sorted(meta.items()))
    con.commit()
    con.close()

    print("Tropper index -> %s" % out)
    print("  source        %s (sha %s)" % (ocr.name, digest))
    print("  page anchor   %s" % (
        "printed = pdf - %d" % offset if offset is not None
        else "unavailable (need the searchable PDF and pdftotext)"))
    print("\n  KTU register  %d entries" % len(ktu))
    print("     checkable against corpus %s : %d" % (corpus_ver, len(checkable)))
    print("     verified                    : %d (%.1f%%)" % (len(verified), rate))
    print("     repaired: %d lost tablet dot, %d fused page number"
          % (rep_dot, rep_fuse))
    print("     unparsed index-shaped lines : %d" % unparsed)
    print("     page list flagged suspect   : %d" % sum(r["pages_suspect"] for r in ktu))
    print("  Subject reg.  %d entries" % len(subjects))
    print("  Root register %d entries  (clean marker %d, in DULAT %d)  UNVERIFIED"
          % (len(roots), clean_marker, sum(r["in_dulat"] for r in roots)))
    if rate < 90 and checkable:
        print("\n  WARNING: KTU verification below 90% — inspect before trusting this build.")
    return 0


# --------------------------------------------------------------------------- lookup


def open_index(args):
    ocr, pdf = resolve_source(args.ocr)
    db = Path(args.out) if args.out else index_db_path(ocr)
    if not db.exists():
        raise SystemExit("no index at %s — run: tropper_index.py build" % db)
    con = connect_ro(db)
    meta = dict(con.execute("select key, value from meta"))
    cur_digest = hashlib.sha256(ocr.read_bytes()).hexdigest()[:16]
    if meta.get("ocr_sha256_16") and meta["ocr_sha256_16"] != cur_digest:
        print("NOTE: the OCR file changed since this index was built — rerun `build`.\n",
              file=sys.stderr)
    return con, meta


def show_pages(pages, meta):
    off = meta.get("page_offset")
    if not pages:
        return "(none)"
    parts = []
    for p in pages.split(","):
        if off:
            parts.append("%s (pdf %d)" % (p, int(p) + int(off)))
        else:
            parts.append(p)
    return ", ".join(parts)


def lookup(args):
    con, meta = open_index(args)
    if args.ktu:
        m = re.match(r"(\d+\.\d+)(?::([IVX]+))?(?::(\d+))?$", args.ktu.strip())
        if not m:
            raise SystemExit("KTU form: 1.14 | 1.14:IV | 1.14:IV:35")
        tab, col, line = m.group(1), m.group(2), m.group(3)
        q = "select column, line, span, pages, verified, pages_suspect from ktu where tablet=?"
        p = [tab]
        if col:
            q += " and column=?"
            p.append(col)
        if line:
            q += " and line=?"
            p.append(line)
        rows = list(con.execute(q + " order by column, cast(line as integer)", p))
        if not rows:
            print("no index entry for KTU %s" % args.ktu)
            return 0
        print("KTU %s — %d indexed reference(s)" % (args.ktu, len(rows)))
        for c, ln, span, pages, ok, susp in rows:
            flag = "" if ok else "   [unverified against corpus]"
            if susp:
                flag += "   [page list suspect]"
            ref = "%s:%s" % (c, ln) if c else ln
            print("  %-12s %s%s%s" % (ref + (span or ""), show_pages(pages, meta), "", flag))
    elif args.term:
        rows = list(con.execute(
            "select term, pages from subjects where term like ? order by term",
            ("%" + args.term + "%",)))
        print("subject register: %d match(es) for %r" % (len(rows), args.term))
        for t, pages in rows[: args.limit]:
            print("  %-46s %s" % (t, show_pages(pages, meta)))
    elif args.root:
        rows = list(con.execute(
            "select root, pages, in_dulat, marker_ok from roots where root like ? order by root",
            ("%" + args.root + "%",)))
        print("root register: %d match(es) for %r   [register is the weakest text"
              " in the book — verify every hit against the scan]" % (len(rows), args.root))
        for r, pages, ind, mk in rows[: args.limit]:
            tag = "" if ind else "  (not a DULAT root)"
            print("  %-8s %s%s" % (r, show_pages(pages, meta), tag))
    elif args.page:
        off = meta.get("page_offset")
        if not off:
            raise SystemExit("no page offset recorded — rebuild with the searchable PDF present")
        print("printed page %s = PDF page %d of %s"
              % (args.page, int(args.page) + int(off), meta.get("searchable_pdf", "?")))
        print("  pdftotext -f %d -l %d '%s' -"
              % (int(args.page) + int(off), int(args.page) + int(off),
                 meta.get("searchable_pdf", "")))
    else:
        for k in sorted(meta):
            print("  %-24s %s" % (k, meta[k]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ocr", help="OCR .txt file or its directory")
    ap.add_argument("--out", help="index sqlite path")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("build", help="parse and validate the registers")
    lk = sub.add_parser("lookup", help="query the index")
    lk.add_argument("--ktu", help="1.14 | 1.14:IV | 1.14:IV:35")
    lk.add_argument("--term", help="German subject term")
    lk.add_argument("--root", help="Ugaritic root")
    lk.add_argument("--page", help="printed page -> PDF page")
    lk.add_argument("--limit", type=int, default=30)
    args = ap.parse_args()
    if args.cmd == "build":
        return build(args)
    if args.cmd == "lookup":
        return lookup(args)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
