"""Seed a reviewed tablet from the 0.2.7 auto-parse (for tablets with no human
gold standard, e.g. KTU 1.1 / 1.2).

For each CUC id we keep exactly one row, choosing the auto variant whose analysis
reconstructs the surface (preferring one with a real DULAT entry); col6 is
re-derived from the DULAT-faithful authority, col4 spacing normalised. Every auto
id is preserved. Prints the rows that still need hand review (no reconstructing
variant, or col4 = ?).

Usage:  build_reviewed_from_auto.py 1.1
"""

import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reconcile_1_4 as R  # noqa: E402
sys.path.insert(0, os.path.join(R.REPO, "agent"))
from linter.lint import reconstruct_surface_from_analysis as RC, normalize_surface as N  # noqa: E402

_SPACING = re.compile(r"^([^\s(]+)\(([IVXLC]+)\)$")  # -h(II) -> -h (II)


def fix_col4(value):
    return "; ".join(_SPACING.sub(r"\1 (\2)", t.strip()) for t in value.split(";"))


def reconstructs(ana, surf):
    if ana.strip() in ("", "?"):
        return False
    try:
        return N(RC(ana)) == N(surf)
    except Exception:  # noqa: BLE001
        return False


def main(tab):
    auto = os.path.join(R.REPO, f"auto_parsing/0.2.7/KTU {tab}.tsv")
    out_path = os.path.join(R.REPO, f"reviewed/KTU {tab}.tsv")

    order, seen, variants, surf = [], set(), collections.defaultdict(list), {}
    for ln in open(auto, encoding="utf-8").read().split("\n"):
        if ln.startswith(f"# KTU {tab}"):
            order.append(("H", ln)); continue
        f = ln.split("\t")
        if len(f) >= 6 and f[0].strip().isdigit():
            tid = f[0].strip()
            variants[tid].append(tuple(f[1:6]))  # surf, ana, dulat, pos, gloss
            surf[tid] = f[1]
            if tid not in seen:
                seen.add(tid); order.append(("T", tid))

    gloss_for, valid = R.build_gloss_authority(variants)

    def choose(tid):
        vs = variants[tid]
        s = surf[tid]
        recon = [v for v in vs if reconstructs(v[1], s)]
        pool = recon or vs
        with_entry = [v for v in pool if v[2].strip() not in ("", "?")]
        return (with_entry or pool)[0]

    out, need = [], []
    for kind, val in order:
        if kind == "H":
            out.append(val); continue
        tid = val
        s, ana, dulat, pos, _g = choose(tid)
        col4 = fix_col4(dulat)
        col4, gloss = R.derive_gloss(tid, col4, gloss_for)
        out.append("\t".join([tid, s, ana, col4, pos, gloss, ""]))
        if not reconstructs(ana, s) or col4 == "?":
            need.append((tid, s, ana, col4))

    open(out_path, "w", encoding="utf-8").write("\n".join(out) + "\n")

    auto_ids = [t for k, t in order if k == "T"]
    rv = set(l.split("\t")[0] for l in out if l.split("\t")[0].isdigit())
    badc = {}
    for l in out:
        f = l.split("\t")
        if not (f and f[0].isdigit()):
            continue
        for p in [x.strip() for x in f[3].split(";")]:
            if p not in ("", "?") and p not in valid:
                badc[p] = badc.get(p, 0) + 1
    print(f"KTU {tab}: ids={len(rv)} missing={len([i for i in auto_ids if i not in rv])} "
          f"invalid_col4={len(badc)} {badc}")
    print(f"  rows needing hand review (no reconstructing variant, or col4=?): {len(need)}")
    for r in need:
        print("   ", r)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "1.1")
