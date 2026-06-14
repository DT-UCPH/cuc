"""Repair invalid col4 DULAT entries in reviewed/KTU 1.5.tsv and 1.6.tsv.

These reviewed tablets have no dropped tokens (the id migration preserved the
full stream), but a handful of col4 values are not real DULAT lemmas:
  * stray sense-number suffixes  (``ʕm (I) 2`` -> ``ʕm (I)``, ``lḥm 3`` -> ``lḥm``)
  * spacing / aleph normalization (``l(I)`` -> ``l (I)``, ``arṣ`` -> ``ảrṣ``)
  * a DULAT lemma written with a leading slash (``/d-k(-k)/`` -> ``d-k(-k)/``)
  * invented entries (šlyṭ tagged as a made-up verb root; krs split into
    k + an invented /r-s/) -> the real DULAT lemmas šlyṭ (n. 'tyrant') and the
    unglossed lemma krs.

Only col4 (and, for the two invented cases, the whole row) changes; reviewed
glosses, POS and comments are left untouched.
"""

import collections
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dulat_lookup import DULAT  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COL4_MAP = {"arṣ": "ảrṣ", "/d-k(-k)/": "d-k(-k)/"}
_SPACING = re.compile(r"^([^\s(]+)\(([IVXLC]+)\)$")  # l(I) -> l (I)

# id -> single replacement row (surface, analysis, col4, pos, gloss, comment)
COLLAPSE = {
    "130131": ("šlyṭ", "šlyṭ/", "šlyṭ", "n. m. sg. cstr.", "tyrant",
               "šlyṭ d šbʕt rảšm 'the tyrant of seven heads' (DULAT n. šlyṭ)."),
    "130258": ("šlyṭ", "šlyṭ/", "šlyṭ", "n. m. sg. cstr.", "tyrant",
               "šlyṭ d šbʕt rảšm 'the tyrant of seven heads' (DULAT n. šlyṭ)."),
    "130138": ("krs", "krs/", "krs", "?", "?",
               "krs: DULAT lemma but unglossed; UNP 'tear to pieces', TCS 'folds (?)'."),
    "130265": ("krs", "krs/", "krs", "?", "?",
               "krs: DULAT lemma but unglossed; UNP 'tear to pieces', TCS 'folds (?)'."),
}


def fix_token(tok):
    tok = tok.strip()
    if tok in ("", "?"):
        return tok
    tok = re.sub(r"\s+\d+$", "", tok)        # drop trailing sense number
    tok = COL4_MAP.get(tok, tok)
    tok = _SPACING.sub(r"\1 (\2)", tok)      # l(I) -> l (I)
    return tok


def fix_col4(value):
    return "; ".join(fix_token(t) for t in value.split(";"))


def load_valid():
    con = sqlite3.connect(DULAT)
    valid = set()
    for l, h in con.execute("SELECT lemma, homonym FROM entries"):
        l = (l or "").strip(); h = (h or "").strip()
        valid.add(l)
        if h:
            valid.add(f"{l} ({h})")
    return valid


def process(path, valid):
    out, collapsed = [], set()
    for ln in open(path, encoding="utf-8").read().split("\n"):
        f = ln.split("\t")
        if not (len(f) >= 2 and f[0].strip().isdigit()):
            out.append(ln)
            continue
        tid = f[0].strip()
        if tid in COLLAPSE:
            if tid in collapsed:
                continue
            collapsed.add(tid)
            surf, ana, col4, pos, gloss, comment = COLLAPSE[tid]
            out.append("\t".join([tid, surf, ana, col4, pos, gloss, comment]))
            continue
        while len(f) < 7:
            f.append("")
        f[3] = fix_col4(f[3])
        out.append("\t".join(f[:7]))
    text = "\n".join(out)
    open(path, "w", encoding="utf-8").write(text)

    bad = collections.Counter()
    for ln in out:
        f = ln.split("\t")
        if not (f and f[0].strip().isdigit()):
            continue
        for t in [x.strip() for x in f[3].split(";")]:
            if t in ("", "?"):
                continue
            if t not in valid:
                bad[t] += 1
    return bad


def main():
    valid = load_valid()
    for tab in ("1.5", "1.6"):
        path = os.path.join(REPO, f"reviewed/KTU {tab}.tsv")
        bad = process(path, valid)
        print(f"KTU {tab}: remaining invalid col4 = {len(bad)} {dict(bad)}")


if __name__ == "__main__":
    main()
