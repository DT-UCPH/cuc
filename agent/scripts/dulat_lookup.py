#!/usr/bin/env python3
"""Deterministic DULAT/UDB lookup helper for KTU 1.5 review.

Usage:
  dulat_lookup.py lemma <text>     - search entries by lemma (normalized)
  dulat_lookup.py form <text>      - search forms by surface text (normalized)
  dulat_lookup.py entry <id>       - dump entry details (pos, gender, summary, forms, translations)
  dulat_lookup.py ref <ref>        - reverse refs for a line, e.g. "CAT 1.5 III:2"
  dulat_lookup.py udb <ref>        - UDB line text for a ref, e.g. "CAT 1.5 III:2"

Database locations are resolved from the DULAT_DB / UDB_DB environment
variables when set; otherwise common repo-relative and sibling-checkout
locations are tried.
"""
import os
import sqlite3
import sys
import unicodedata

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _find_db(env_var, candidates):
    path = os.environ.get(env_var)
    if path:
        return os.path.expanduser(path)
    for cand in candidates:
        cand = os.path.expanduser(cand)
        if os.path.exists(cand):
            return cand
    sys.exit(f"{env_var} not set and no database found; tried: {', '.join(candidates)}")


DULAT = _find_db("DULAT_DB", [
    os.path.join(REPO, "agent", "sources", "dulat_cache.sqlite"),
    os.path.join(REPO, "sources", "dulat_cache.sqlite"),
    os.path.join(REPO, "..", "dulat", "app", "data", "dulat_cache.sqlite"),
    "~/projects/dulat/app/data/dulat_cache.sqlite",
])
UDB = _find_db("UDB_DB", [
    os.path.join(REPO, "agent", "udb_cache.sqlite"),
    os.path.join(REPO, "agent", "sources", "udb_cache.sqlite"),
    os.path.join(REPO, "sources", "udb_cache.sqlite"),
    os.path.join(REPO, "..", "dulat", "app", "udb", "udb_cache.sqlite"),
    "~/projects/dulat/app/udb/udb_cache.sqlite",
])

ALEPH = {"ả": "a", "ỉ": "i", "ủ": "u", "Ả": "a", "Ỉ": "i", "Ủ": "u",
         "á": "a", "í": "i", "ú": "u", "à": "a", "ì": "i", "ù": "u"}
AYIN = {"ʿ": "ˤ", "ʕ": "ˤ"}


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    out = []
    for ch in s:
        ch = ALEPH.get(ch, ch)
        ch = AYIN.get(ch, ch)
        out.append(ch)
    return "".join(out).lower()


def lemma_search(q):
    con = sqlite3.connect(DULAT)
    nq = norm(q)
    rows = con.execute("SELECT entry_id, lemma, homonym, pos, gender, summary FROM entries").fetchall()
    hits = [r for r in rows if norm(r[1]) == nq]
    if not hits:
        hits = [r for r in rows if nq in norm(r[1])][:25]
    for r in hits:
        print(f"#{r[0]}\t{r[1]}{(' ('+r[2]+')') if r[2] else ''}\t[{r[3] or ''}|{r[4] or ''}]\t{(r[5] or '')[:140]}")


def form_search(q):
    con = sqlite3.connect(DULAT)
    nq = norm(q)
    rows = con.execute(
        "SELECT f.entry_id, e.lemma, e.homonym, e.pos, f.text, f.morphology FROM forms f JOIN entries e ON e.entry_id=f.entry_id").fetchall()
    hits = [r for r in rows if norm(r[4]) == nq]
    for r in hits:
        print(f"#{r[0]}\t{r[1]}{(' ('+r[2]+')') if r[2] else ''}\t[{r[3] or ''}]\tform={r[4]}\tmorph={r[5] or ''}")
    if not hits:
        print("(no exact form match)")


def entry_dump(eid):
    con = sqlite3.connect(DULAT)
    e = con.execute("SELECT entry_id, lemma, homonym, pos, gender, summary FROM entries WHERE entry_id=?", (eid,)).fetchone()
    if not e:
        print("not found"); return
    print(f"#{e[0]} {e[1]}{(' ('+e[2]+')') if e[2] else ''} [{e[3] or ''}|{e[4] or ''}]")
    print(f"summary: {(e[5] or '')[:400]}")
    for t in con.execute("SELECT text FROM translations WHERE entry_id=? LIMIT 8", (eid,)):
        print(f"  tr: {t[0][:160]}")
    for f in con.execute("SELECT text, morphology FROM forms WHERE entry_id=? LIMIT 25", (eid,)):
        print(f"  form: {f[0]}\t{f[1] or ''}")
    for s in con.execute("SELECT * FROM stems WHERE entry_id=? LIMIT 10", (eid,)):
        print(f"  stem: {s}")


def ref_lookup(ref):
    con = sqlite3.connect(UDB)
    dcon = sqlite3.connect(DULAT)
    for key in (ref, ref.replace("KTU", "CAT"), "CAT " + ref, "KTU " + ref):
        rows = con.execute(
            "SELECT entry_id, payload FROM ktu_to_dulat WHERE ktu_ref=?", (key,)).fetchall()
        if rows:
            print(f"[{key}]")
            for eid, payload in rows:
                e = dcon.execute(
                    "SELECT lemma, homonym, pos, gender, summary FROM entries WHERE entry_id=?",
                    (eid,)).fetchone()
                if e:
                    print(f"#{eid}\t{e[0]}{(' ('+e[1]+')') if e[1] else ''}\t[{e[2] or ''}|{e[3] or ''}]\t{(e[4] or '')[:100]}")
                else:
                    print(f"#{eid}\t{payload[:120]}")
            return
    print("(no reverse refs)")


def udb_line(ref):
    con = sqlite3.connect(UDB)
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    if "cuc_lines" in tables:
        cols = [c[1] for c in con.execute("PRAGMA table_info(cuc_lines)")]
        for key in (ref, ref.replace("KTU", "CAT"), "CAT " + ref, "KTU " + ref):
            rows = con.execute("SELECT * FROM cuc_lines WHERE ktu_ref=?", (key,)).fetchall()
            for r in rows:
                print(dict(zip(cols, r)))
            if rows:
                return
    print("(no udb line)")


if __name__ == "__main__":
    cmd, arg = sys.argv[1], " ".join(sys.argv[2:])
    {"lemma": lemma_search, "form": form_search,
     "entry": lambda a: entry_dump(int(a)), "ref": ref_lookup, "udb": udb_line}[cmd](arg)
