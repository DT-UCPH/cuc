"""One-off reconciliation of reviewed/KTU 1.4.tsv against the 0.2.7 auto-parse.

Fixes three integrity problems introduced during column-by-column review:
  1. Dropped tokens — every CUC id present in the auto-parse must be present
     in the reviewed file (20 ids had been lost to over-eager grep dedup).
  2. Invented DULAT entries — col4 must name a real DULAT lemma (or "?"); a
     dozen entries (nblảt, …) were remapped to the real lemma or reverted to "?".
  3. Non-DULAT glosses — col6 is re-derived from the project's DULAT-faithful
     authority (the auto-parser's own gloss for that id+entry, else the corpus
     consensus gloss for the entry, else the DULAT DB translation).

Run with the agent venv (needs only stdlib + the DULAT sqlite cache).
"""

import collections
import glob
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dulat_lookup import DULAT  # noqa: E402  (portable DULAT_DB resolver)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUTO = os.path.join(REPO, "auto_parsing/0.2.7/KTU 1.4.tsv")
REV = os.path.join(REPO, "reviewed/KTU 1.4.tsv")

# --- col4 remaps: invented/invalid entry -> real DULAT lemma (or "?") ----------
REMAP = {
    "nblảt": "nblủ",
    "ảtnt": "ảtn (I)",
    "mrỉ": "mrủ (I)",
    "lḥm 3": "lḥm",
    "/n-d-y/": "/n-d-d/",
    "/m-r-r/": "/m-r(-r)/ (I)",
    "sdt": "?",
    "/ʕ-s/": "?",
    "dbt": "?",
    "ʕdr": "?",
}

# --- full-row overrides keyed by id: (surface, analysis, col4, pos, gloss|None, comment) -
OVERRIDE = {
    # corrupted amht rows (a stray sed had shifted their fields)
    "128835": ("amht", "am&h(t/t", "ảmt (I)", "n. f. pl. abs. gen.", None,
               "'the lewdness of handmaids'."),
    "128844": ("amht", "am&h(t/t", "ảmt (I)", "n. f. pl. abs. nom.", None,
               "'and in it the lewdness of handmaids'."),
    # lḥmd is a real DULAT lemma (no gloss given); do not split into l+ḥmd
    "129373": ("lḥmd", "lḥmd[", "lḥmd", "vb", "?",
               "DULAT lists lḥmd at this line but gives no gloss."),
    # td = /n-d-d/ (DULAT cites td ỉšt b bhtm here), not /n-d-y/
    "129611": ("td", "!t!(nd(d[", "/n-d-d/", "vb G prefc. 3 f. sg.", None,
               "'the fire went out in the palace' (DULAT cites td ỉšt b bhtm s.v. /n-d-d/)."),
    # mrr -> /m-r(-r)/ (I)
    "129777": ("mrr", "mr[r", "/m-r(-r)/ (I)", "vb G suffc. 3 m. sg.", None,
               "DULAT cites mr[r at this line s.v. /m-r(-r)/ (I)."),
    # invented -> revert to ? (no DULAT entry for the surface as tokenized)
    "128594": ("sdt", "?", "?", "?", "?",
               "DULAT attests msdt ảrṣ here; sdt may belong to msdt 'foundation(s)'."),
    "129079": ("ˤst", "?", "?", "?", "?", "Broken (ʕs[); no DULAT entry."),
    "129253": ("dbt", "?", "?", "?", "?", "No DULAT entry for dbt."),
    "129757": ("ˤdr", "?", "?", "?", "?", "Broken; no DULAT entry."),
}

# --- analysis-only fixes (keep my col4/pos/comment, just make it reconstruct) ---
ANALYSIS_FIX = {
    # nblat: encode lexeme nblủ (surface a), all five attestations
    "129572": "nbl(ủ&a/t", "129583": "nbl(ủ&a/t", "129593": "nbl(ủ&a/t",
    "129603": "nbl(ủ&a/t", "129615": "nbl(ủ&a/t",
    # m|ria MERGE -> mrủ (I); both rows reconstruct the joined surface "mria"
    "129651": "mr(ủ&i&a/", "129652": "mr(ủ&i&a/",
    # hdxt: hd (Haddu) + broken x t kept as surface-only
    "129881": "hd/&x&t",
}

# --- 20 dropped tokens to restore: id -> (surface, analysis, col4, pos, gloss|None, comment) -
MISSING = {
    "128780": ("dr", "dr/", "dr", "n. m. sg. abs. gen.", None,
               "w dr dr 'the (eternal) assembly'."),
    "129092": ("ks", "ks(I)/", "ks (I)", "n. m. sg. cstr. gen.", None,
               "b ks ḫrṣ 'in a cup of gold'."),
    "129093": ("ḫrṣ", "ḫrṣ/", "ḫrṣ", "n. m. sg. cstr. gen.", None, "'(cup of) gold'."),
    "129265": ("ṣḥ", "ṣḥ[", "/ṣ-ḥ/", "vb G impv. m. sg.", None, None),
    "129302": ("ttn", "!t!(ytn[:w", "/y-t-n/", "vb G prefc. 3 m. pl.", None, None),
    "129333": ("ṣḥ", "ṣḥ[", "/ṣ-ḥ/", "vb G impv. m. sg.", None, None),
    "129360": ("ṣḥ", "ṣḥ[", "/ṣ-ḥ/", "vb G impv. m. sg.", None, None),
    "129361": ("ḫrn", "ḫrn/", "ḫrn", "n. m. sg. abs. acc.", None,
               "ṣḥ ḫrn b bhtk 'summon a work-gang into your house'."),
    "129411": ("lḥm", "lḥm[:w", "/l-ḥ-m/ (I)", "vb G suffc. 3 m. pl.", None, None),
    "129427": ("rmm", "rmm[:l", "/r-m/", "vb L impv. m. sg.", None, None),
    "129486": ("tṯb", "!t!(yṯb[:w", "/y-ṯ-b/", "vb G prefc. 3 m. pl.", None, None),
    "129660": ("ṣḥ", "ṣḥ[", "/ṣ-ḥ/", "vb G impv. m. sg.", None, None),
    "129668": ("ṣḥ", "ṣḥ[", "/ṣ-ḥ/", "vb G impv. m. sg.", None, None),
    "129703": ("lḥm", "lḥm[:w", "/l-ḥ-m/ (I)", "vb G suffc. 3 m. pl.", None, None),
    "129716": ("tšty", "!t!šty[:w", "/š-t-y/", "vb G prefc. 3 m. pl.", None, None),
    "129748": ("rḥq", "rḥq[", "/r-ḥ-q/", "vb G impv. m. sg.", None, None),
    "129780": ("ˤrb", "ˤrb[:w", "/ʕ-r-b/ (I)", "vb G suffc. 3 m. pl.", None, None),
    "129890": ("qdm", "qdm[:d:w", "/q-d-m/", "vb D suffc. 3 m. pl.", None, None),
    "129953": ("ˤn", "ˤn[", "/ʕ-n/", "vb G impv. m. sg.", None, None),
    "129957": ("bnġlmt", "b~n ġlmt(II)/", "b; ġlmt (II)",
               "prep. + encl. -n; n. f. sg. abs.", None,
               "bn ġlmt 'in the gloom' (// bn ẓlmt)."),
}


def parse_auto():
    order, seen, rows, section = [], set(), collections.defaultdict(list), {}
    cur = None
    for ln in open(AUTO, encoding="utf-8").read().split("\n"):
        if ln.startswith("# KTU 1.4"):
            order.append(("H", ln)); cur = ln; continue
        f = ln.split("\t")
        if len(f) >= 6 and f[0].strip().isdigit():
            tid = f[0].strip()
            rows[tid].append(tuple(f[1:6]))  # surface, analysis, dulat, pos, gloss
            if tid not in seen:
                seen.add(tid); order.append(("T", tid)); section[tid] = cur
    return order, rows, section


def parse_reviewed():
    rows = collections.defaultdict(list)
    for ln in open(REV, encoding="utf-8").read().split("\n"):
        f = ln.split("\t")
        if len(f) >= 2 and f[0].strip().isdigit():
            while len(f) < 7:
                f.append("")
            rows[f[0].strip()].append(f[:7])
    return rows


def build_gloss_authority(auto_rows):
    per_ie = {}
    for tid, variants in auto_rows.items():
        for surf, ana, dulat, pos, gloss in variants:
            d = (dulat or "").strip(); g = (gloss or "").strip()
            if d and d != "?" and g and g != "?":
                per_ie.setdefault((tid, d), g)
    consensus = collections.defaultdict(collections.Counter)
    for p in glob.glob(os.path.join(REPO, "auto_parsing/0.2.7/*.tsv")):
        for ln in open(p, encoding="utf-8"):
            f = ln.split("\t")
            if len(f) >= 6 and f[0].strip().isdigit():
                d = f[3].strip(); g = f[5].strip()
                if d and d != "?" and g and g != "?":
                    consensus[d][g] += 1
    consensus = {d: c.most_common(1)[0][0] for d, c in consensus.items()}
    con = sqlite3.connect(DULAT)
    db_tr = {}
    for eid, t in con.execute(
        "SELECT entry_id, text FROM translations ORDER BY entry_id, rowid"):
        if t:
            db_tr.setdefault(eid, t)
    ent2eid = {}
    for eid, lemma, hom in con.execute("SELECT entry_id, lemma, homonym FROM entries"):
        lemma = (lemma or "").strip(); hom = (hom or "").strip()
        ent2eid.setdefault(lemma, eid)
        if hom:
            ent2eid.setdefault(f"{lemma} ({hom})", eid)
    valid = set(ent2eid)

    def gloss_for(tid, entry):
        entry = entry.strip()
        if entry in ("", "?"):
            return "?"
        # 1) the auto-parser's own contextual gloss for this exact id+entry;
        # 2) DULAT's primary (first) translation for the entry;
        # 3) corpus-consensus gloss as a last resort.
        eid = ent2eid.get(entry)
        g = per_ie.get((tid, entry)) or (db_tr.get(eid) if eid else None) \
            or consensus.get(entry)
        return g if g else "?"

    return gloss_for, valid


def derive_gloss(tid, col4, gloss_for):
    parts = [p.strip() for p in col4.split(";")]
    mapped = [REMAP.get(p, p) for p in parts]
    new_col4 = "; ".join(mapped)
    new_gloss = "; ".join(gloss_for(tid, p) for p in mapped)
    return new_col4, new_gloss


def main():
    order, auto_rows, _ = parse_auto()
    rev_rows = parse_reviewed()
    gloss_for, valid = build_gloss_authority(auto_rows)

    out, emitted = [], set()
    changed_gloss = 0
    for kind, val in order:
        if kind == "H":
            out.append(val); continue
        tid = val
        if tid in emitted:
            continue
        emitted.add(tid)
        if tid in OVERRIDE:
            surf, ana, col4, pos, gloss, comment = OVERRIDE[tid]
            col4, dgloss = derive_gloss(tid, col4, gloss_for)
            gloss = gloss if gloss is not None else dgloss
            out.append("\t".join([tid, surf, ana, col4, pos, gloss, comment or ""]))
        elif tid in MISSING:
            surf, ana, col4, pos, gloss, comment = MISSING[tid]
            col4, dgloss = derive_gloss(tid, col4, gloss_for)
            gloss = gloss if gloss is not None else dgloss
            out.append("\t".join([tid, surf, ana, col4, pos, gloss, comment or ""]))
        else:
            for row in rev_rows[tid]:
                _id, surf, ana, col4, pos, gloss, comment = row[:7]
                ana = ANALYSIS_FIX.get(tid, ana)
                new_col4, new_gloss = derive_gloss(tid, col4, gloss_for)
                if new_gloss != gloss:
                    changed_gloss += 1
                out.append("\t".join([tid, surf, ana, new_col4, pos, new_gloss, comment]))

    text = "\n".join(out) + "\n"
    open(REV + ".new", "w", encoding="utf-8").write(text)

    # ---- validation ----
    auto_ids = [t for k, t in order if k == "T"]
    rev_ids = [l.split("\t")[0] for l in out
               if l and l.split("\t")[0].isdigit()]
    rev_id_set = set(rev_ids)
    missing = [i for i in auto_ids if i not in rev_id_set]
    bad_col4 = collections.Counter()
    bad_fields = 0
    for l in out:
        f = l.split("\t")
        if not (f and f[0].isdigit()):
            continue
        if len(f) != 7:
            bad_fields += 1
        for p in [p.strip() for p in f[3].split(";")]:
            if p in ("", "?"):
                continue
            if p not in valid:
                bad_col4[p] += 1
    print(f"auto ids: {len(set(auto_ids))}  reviewed ids: {len(rev_id_set)}")
    print(f"MISSING tokens: {len(missing)} {missing}")
    print(f"bad field-count rows: {bad_fields}")
    print(f"glosses changed: {changed_gloss}")
    print(f"invalid col4 entries: {len(bad_col4)} {dict(bad_col4)}")


if __name__ == "__main__":
    main()
