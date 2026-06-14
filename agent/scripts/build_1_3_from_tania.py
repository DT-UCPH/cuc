"""Build reviewed/KTU 1.3.tsv by aligning Tania's gold-standard analyses onto
the CUC 0.2.7 token stream.

Tania's file (reviewed/KTU_1.3_original.txt) carries the authoritative
morphological parsing (col3), but in an older id numbering (136937+) and with
inline "# ..." notes. The latest CUC (0.2.7) numbers 1.3 as 127265-128456 and
sets the tokenization we must follow. We align the two surface sequences with
difflib, copy Tania's analysis onto each 0.2.7 token, take DULAT col4/POS from
the auto-parse, derive the gloss from the DULAT-faithful authority, and keep
Tania's note as the comment.

Non-1:1 alignment blocks (split/merge/notation/sign differences) are handled by
OVERRIDE, keyed by 0.2.7 id.
"""

import difflib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reconcile_1_4 as R  # noqa: E402  (reuse DULAT gloss authority)
sys.path.insert(0, os.path.join(R.REPO, "agent"))
from linter.lint import normalize_surface  # noqa: E402

TANIA = os.path.join(R.REPO, "reviewed/KTU_1.3_original.txt")
AUTO = os.path.join(R.REPO, "auto_parsing/0.2.7/KTU 1.3.tsv")
OUT = os.path.join(R.REPO, "reviewed/KTU 1.3.tsv")

# 0.2.7 id -> (analysis, col4, pos, comment). gloss derived from col4.
# Covers the difflib non-equal blocks (merged/split/notation/sign differences).
OVERRIDE = {
    "127353": ("pdry/", "pdry", "DN f. sg. abs. gen.", "pdry (Tania pdr<y>)."),
    "127390": ("bn(I)/&x", "bn (I)", "n. m. sg. cstr. gen.", "bnx: bn + broken sign (Tania bn+x)."),
    "127538": ("ṯlḥn/t", "ṯlḥn", "n. m. sg. cstr. gen.", "ṯlḥnt 'table' (Tania ṯlḥ<t>)."),
    "127567": ("ym(II)/&x&x&x&x&x&x", "ym (II)", "n. m. sg. abs. gen.", "ymxxxxxx: ym + broken signs."),
    "127847": ("(ḥ&hš[+k", "/ḥ-š/ (I)", "vb G impv. m. sg. + 2 m. sg. suff.", "hšk 'hurry!' (Tania ḥš; sign h/ḥ)."),
    "127872": ("!t!(ydˤ(I)[", "/y-d-ʕ/ (I)", "vb G prefc. 3 f. sg.", "tdˤ 'she knows' (Tania td+ˤ)."),
    "127932": ("b šm(m(I)/m", "b; šmm (I)", "prep.; n. m. du. abs. gen.", "bšmm 'in the heavens' (Tania b+šmm)."),
    "128041": ("l(I) bˤl(II)/", "l (I); bʕl (II)", "prep.; DN m. sg. gen.", "lbˤl 'to Baal' (Tania l+bˤl)."),
    "128184": ("w", "w", "conj.", ""),
    "128185": ("!t!ˤn(y[", "/ʕ-n-y/ (I)", "vb G prefc. 3 f. sg.", "w tˤn 'and she answered' (Tania merged w tˤn)."),
    "128211": ("!(ʔ&a!mḫṣ[&x&x&x", "/m-ḫ-ṣ/", "vb G prefc. 1 c. sg.", "amḫṣxxx: amḫṣ + broken signs."),
    "128248": ("ḥkm/", "ḥkm", "n. m. sg. abs. nom.", "ḥkm (Tania read hkm; sign h/ḥ)."),
    "128429": ("kṯr(III)/", "kṯr (III)", "DN m. sg. abs. nom.", "kṯr (Tania kṯ<r>)."),
    "128456": ("qrd/m", "qrd (I)", "n. m. pl. abs. acc.", "qrdm 'heroes' (not present in Tania's copy)."),
}

# equal-block tokens whose aligned analysis needs adjusting to reconstruct the
# 0.2.7 surface (aleph a/ʔ notation, unwritten weak radicals); auto col4 kept.
ANALYSIS_FIX = {
    "127372": "kl(ʔ&a[t=",       # klat 'both' (Tania klʔt)
    "127688": "!(ʔ&i!bġy[+h",    # ibġyh 'I seek it'
    "127723": "!t!](n]š(ʔ[&u",   # tšu 'she lifts' (assimilated n)
    "127814": "!y!ˤny[n",        # yˤnyn 'he answers'
}

_SPACING = re.compile(r"^([^\s(]+)\(([IVXLC]+)\)$")  # -h(II) -> -h (II)


def _fix_col4(value):
    return "; ".join(_SPACING.sub(r"\1 (\2)", t.strip()) for t in value.split(";"))


def parse_tania():
    rows = []
    for ln in open(TANIA, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if ln.startswith("#") or ln.startswith("id\t") or not ln.strip():
            continue
        f = ln.split("\t")
        if not (f and f[0].strip().isdigit()):
            continue
        surf = f[1] if len(f) > 1 else ""
        raw = f[2] if len(f) > 2 else ""
        note = ""
        if "#" in raw:
            ana, note = raw.split("#", 1)
            ana, note = ana.strip(), note.strip()
        else:
            ana = raw.strip()
        rows.append({"surf": surf, "ana": ana, "note": note})
    return rows


def parse_auto_stream():
    """Return ordered stream of ('H', headerline) / ('T', id), plus id->surface
    and id->(dulat,pos,gloss) first variant."""
    order, seen, surf, meta = [], set(), {}, {}
    for ln in open(AUTO, encoding="utf-8").read().split("\n"):
        if ln.startswith("# KTU 1.3"):
            order.append(("H", ln)); continue
        f = ln.split("\t")
        if len(f) >= 6 and f[0].strip().isdigit():
            tid = f[0].strip()
            if tid not in seen:
                seen.add(tid); order.append(("T", tid))
                surf[tid] = f[1]; meta[tid] = (f[3], f[4], f[5])
    return order, surf, meta


def main():
    tania = parse_tania()
    order, auto_surf, auto_meta = parse_auto_stream()
    auto_ids = [t for k, t in order if k == "T"]

    # align normalized surface sequences
    t_norm = [normalize_surface(r["surf"]) for r in tania]
    a_norm = [normalize_surface(auto_surf[i]) for i in auto_ids]
    sm = difflib.SequenceMatcher(a=t_norm, b=a_norm, autojunk=False)
    # map auto-index -> tania row (only for equal blocks)
    a2t = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                a2t[j1 + k] = tania[i1 + k]

    gloss_for, valid = R.build_gloss_authority(_auto_variant_rows())

    auto_index = {tid: n for n, tid in enumerate(auto_ids)}
    out = []
    for kind, val in order:
        if kind == "H":
            out.append(val); continue
        tid = val
        dulat, pos, _ = auto_meta[tid]
        if tid in OVERRIDE:
            ana, col4, pos, comment = OVERRIDE[tid]
        else:
            tr = a2t.get(auto_index[tid])
            comment = ""
            if tr is not None:
                ana = tr["ana"] or auto_surf[tid]
                comment = tr["note"]
            else:
                ana = auto_surf[tid]  # unaligned: fall back to surface, flag it
                comment = "ALIGN?"
            ana = ANALYSIS_FIX.get(tid, ana)
            col4 = dulat
        col4 = _fix_col4(col4)
        col4, gloss = R.derive_gloss(tid, col4, gloss_for)
        out.append("\t".join([tid, auto_surf[tid], ana, col4, pos, gloss, comment]))

    open(OUT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    _validate(out, auto_ids, valid)


def _auto_variant_rows():
    """All auto variant rows per id for 1.3 (for gloss authority)."""
    import collections
    rows = collections.defaultdict(list)
    for ln in open(AUTO, encoding="utf-8").read().split("\n"):
        f = ln.split("\t")
        if len(f) >= 6 and f[0].strip().isdigit():
            rows[f[0].strip()].append(tuple(f[1:6]))
    return rows


def _validate(out, auto_ids, valid):
    from linter.lint import reconstruct_surface_from_analysis
    rv, badc, recon, align = [], {}, [], 0
    last = None
    for l in out:
        f = l.split("\t")
        if not (f and f[0].isdigit()):
            continue
        if f[0] != last:
            rv.append(f[0]); last = f[0]
        if len(f) > 6 and f[6] == "ALIGN?":
            align += 1
        for p in [x.strip() for x in f[3].split(";")]:
            if p not in ("", "?") and p not in valid:
                badc[p] = badc.get(p, 0) + 1
        comment = f[6] if len(f) > 6 else ""
        if f[2].strip() in ("", "?") or "MERGE" in comment:
            continue
        try:
            rec = reconstruct_surface_from_analysis(f[2])
            if normalize_surface(rec) != normalize_surface(f[1]):
                recon.append((f[0], f[1], f[2], rec))
        except Exception as e:  # noqa: BLE001
            recon.append((f[0], f[1], f[2], str(e)))
    rvset = set(rv)
    print("missing vs auto:", [i for i in auto_ids if i not in rvset])
    print("unaligned (ALIGN?) tokens:", align)
    print("invalid col4:", len(badc), dict(list(badc.items())[:20]))
    print("non-MERGE reconstruct mismatches:", len(recon))
    for r in recon[:40]:
        print("   ", r)


if __name__ == "__main__":
    main()
