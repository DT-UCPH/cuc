"""Fix pre-existing reconstruction mismatches in reviewed/KTU 1.5 & 1.6.

Genuine analysis typos:
  * 130244 nšt   : nšy[t -> nš(y[t   (hide the unwritten weak y)
  * 130263 ttrp  : drop a stray surface 'p' (analysis reconstructed ttrpp)
  * 130388 šmḥy  : mḫy -> mḥy        (surface has ḥ, not ḫ)
Impossible alternative reading:
  * 130375 aṣḥ   : drop the 3 m. sg. yṣḥ row (surface is aṣḥ = 1 c. sg.);
                   keep the UNP note on the surviving row.
Broken signs (x = illegible sign): encode the x's as surface-only &x so the
analysis reconstructs the recorded surface.
  * 130389, 130431, 130708 (1.5) and 131124 (1.6).
"""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (id, old_analysis) -> new_analysis  ; new_analysis == None means delete the row
ANALYSIS = {
    ("130244", "nšy[t"): "nš(y[t",
    ("130263", "!t!]t]rp(y[p:d:w"): "!t!]t]rp(y[:d:w",
    ("130263", "!t!]t]rp(y[p:d"): "!t!]t]rp(y[:d",
    ("130388", "!!]š]mḫy["): "!!]š]mḥy[",
    ("130375", "!y!ṣḥ["): None,  # drop impossible 3 m. sg. reading of surface aṣḥ
    ("130389", "tbˤ["): "&x&x&x&x&x&x&x&x&x&x&xtbˤ[",
    ("130389", "!!tbˤ[/"): "&x&x&x&x&x&x&x&x&x&x&x!!tbˤ[/",
    ("130431", "(hlk["): "(hlk[&x",
    ("130708", "il(I)/"): "il(I)/&x&x",
    ("131124", "l(I) ˤgl(I)/+h"): "l(I)&x ˤgl(I)/+h",
}
# id -> replacement comment (applied to surviving rows of that id)
COMMENT = {"130375": "Surface aṣḥ (1 c. sg.); UNP reads wyṣḥ (3 m. sg.)."}


def process(path):
    out = []
    for ln in open(path, encoding="utf-8").read().split("\n"):
        f = ln.split("\t")
        if not (len(f) >= 3 and f[0].strip().isdigit()):
            out.append(ln)
            continue
        tid, ana = f[0].strip(), f[2]
        key = (tid, ana)
        if key in ANALYSIS:
            new = ANALYSIS[key]
            if new is None:
                continue  # drop row
            f[2] = new
        if tid in COMMENT:
            while len(f) < 7:
                f.append("")
            f[6] = COMMENT[tid]
        out.append("\t".join(f))
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main():
    sys.path.insert(0, os.path.join(REPO, "agent"))
    from linter.lint import reconstruct_surface_from_analysis, normalize_surface
    for tab in ("1.5", "1.6"):
        path = os.path.join(REPO, f"reviewed/KTU {tab}.tsv")
        process(path)
        bad = []
        for ln in open(path, encoding="utf-8"):
            f = ln.rstrip("\n").split("\t")
            if not (f and f[0].isdigit()):
                continue
            surf, ana = f[1], f[2]
            comment = f[6] if len(f) > 6 else ""
            if ana.strip() in ("", "?") or "MERGE" in comment:
                continue
            try:
                rec = reconstruct_surface_from_analysis(ana)
            except Exception as e:  # noqa: BLE001
                bad.append((f[0], surf, ana, str(e)))
                continue
            if normalize_surface(rec) != normalize_surface(surf):
                bad.append((f[0], surf, ana, rec))
        print(f"KTU {tab}: non-MERGE reconstruct mismatches = {len(bad)}")
        for b in bad:
            print("   ", b)


if __name__ == "__main__":
    main()
