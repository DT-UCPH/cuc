"""Align EUPT's own token-level morphology (module_records.data_json -> words[])
to cuc-origin rows, and report where they disagree.

EUPT tag conventions that differ from ours:
    GN = Gottesname   -> our DN      (NOT our GN!)
    ON = Ortsname     -> our GN / TN
    PN = Personenname -> our PN
    St.cs.            -> cstr.
    G-SK              -> vb G suffc.
    G-PKL/PKK/PKx     -> vb G prefc. (long / short / unspecified)
"""
import csv, json, os, re, sqlite3, collections, sys

def _repo_root(start):
    for c in [start, *start.parents]:
        if (c / "reviewed").is_dir() and (c / "agent").is_dir():
            return c
    raise SystemExit("run from inside the cuc-origin repo")


import pathlib
R = str(_repo_root(pathlib.Path.cwd().resolve()))
sys.path.insert(0, os.path.join(R, "agent"))
from project_paths import get_project_paths  # noqa: E402

MODULES_DB = os.environ.get("CUC_MODULES_DB") or str(get_project_paths().default_modules_db())
mod = sqlite3.connect(f"file:{MODULES_DB}?mode=ro", uri=True)
mod.row_factory = sqlite3.Row
if not mod.execute("select count(*) from module_records where module_id='EUPT_vocalisation' "
                   "and data_json is not null and data_json != ''").fetchone()[0]:
    raise SystemExit(
        f"{MODULES_DB} has no EUPT_vocalisation records with data_json.\n"
        "The repo-local modules cache is an older snapshot without the EUPT layer.\n"
        "Point CUC_MODULES_DB at the current modules_cache.sqlite, e.g.\n"
        "  CUC_MODULES_DB=<path>/modules_cache.sqlite python3 <this script> 1.14")

TABLET = sys.argv[1] if len(sys.argv) > 1 else "1.14"
COLS = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None

# ---------- de-vocalise an EUPT form to the consonantal skeleton ----------
VOWELS = "aeiouāēīōūâêîôûăĕĭŏŭ"
CONS_MAP = {"ˁ": "ˤ", "ʕ": "ˤ"}

def skel(form):
    """EUPT vocalised form -> consonantal skeleton in corpus orthography.

    Aleph (ˀ) is written in the corpus as the vowel letter a/i/u, so ˀ is
    dropped and the vowel that follows it is kept; all other vowels drop.
    """
    s = re.sub(r"[\[\]⸢⸣!?()<>{}/]", "", form or "")
    out = []
    keep_next_vowel = False
    for ch in s:
        low = ch.lower()
        base = {"ā": "a", "â": "a", "ē": "e", "ê": "e", "ī": "i", "î": "i",
                "ō": "o", "ô": "o", "ū": "u", "û": "u"}.get(low, low)
        if base == "ˀ":
            keep_next_vowel = True
            continue
        if base in VOWELS:
            if keep_next_vowel:
                out.append("i" if base == "e" else "u" if base == "o" else base)
                keep_next_vowel = False
            continue
        keep_next_vowel = False
        if base == "v":            # EUPT's unknown-vowel placeholder
            continue
        out.append(CONS_MAP.get(base, base))
    return "".join(out)

# ---------- EUPT words per line ----------
eupt = collections.defaultdict(list)
for r in mod.execute("select ref_norm, data_json from module_records "
                     "where module_id='EUPT_vocalisation' and ref_norm like ?",
                     (f"CAT {TABLET} %",)):
    try:
        j = json.loads(r["data_json"] or "{}")
    except Exception:
        continue
    m = re.match(r"CAT \S+ ([IVX]+):(\d+)", r["ref_norm"])
    if not m:
        continue
    key = (m.group(1), int(m.group(2)))
    for w in (j.get("words") or []):
        eupt[key].append({"form": w.get("form", ""), "skel": skel(w.get("form", "")),
                          "morph": (w.get("morph") or "").strip(),
                          "lemma": (w.get("lemma") or "").strip()})

# ---------- corpus rows ----------
HDR = re.compile(r"^# KTU \S+ ([IVX]+):(\d+)")
rows = collections.defaultdict(list)
loc = None
path = f"{R}/reviewed/KTU {TABLET}.tsv"
for raw in open(path, encoding="utf-8"):
    f = raw.rstrip("\n").split("\t")
    if f[0].startswith("#"):
        m = HDR.match(f[0]); loc = (m.group(1), int(m.group(2))) if m else None
        continue
    if not f[0].isdigit() or loc is None:
        continue
    g = lambda i: f[i] if len(f) > i else ""
    rows[loc].append({"id": f[0], "surf": f[1], "ana": g(3), "dul": g(4),
                      "pos": g(5), "gloss": g(6), "cmt": g(7)})

# ---------- compare ----------
def our_class(pos):
    p = (pos or "").strip()
    for t in ("DN", "PN", "GN", "TN"):
        if p.startswith(t):
            return "DN" if t == "DN" else "PN" if t == "PN" else "GN"
    if p.startswith("vb"):
        return "vb"
    return None if p in ("", "?") else "other"

def eupt_class(morph):
    m = morph or ""
    if m.startswith("GN"): return "DN"      # Gottesname
    if m.startswith("PN"): return "PN"
    if m.startswith(("ON", "TN")): return "GN"
    if re.match(r"[GDLNŠ]t?(pass)?-(SK|PK|Imp|Inf|Ptz)", m) or m.startswith(("G-", "D-", "Š-", "N-", "L-", "Gt-", "tD-")):
        return "vb"
    return None if not m else "other"

def _uninformative(oc, ec):
    """A bare EUPT case tag ('nominal') cannot confirm or deny proper-noun status,
    so ours=DN/PN/GN vs EUPT=other is not evidence of a conflict."""
    return ec == "other" and oc in ("DN", "PN", "GN")


stat = collections.Counter()
dis = []
for key, toks in sorted(rows.items()):
    if COLS and key[0] not in COLS:
        continue
    ew = eupt.get(key, [])
    by_skel = collections.defaultdict(list)
    for w in ew:
        by_skel[w["skel"]].append(w)
    for t in toks:
        cand = by_skel.get(t["surf"].lower())
        if not cand:
            stat["no-eupt-match"] += 1
            continue
        w = cand[0]
        stat["matched"] += 1
        oc, ec = our_class(t["pos"]), eupt_class(w["morph"])
        if oc and ec and oc != ec and not _uninformative(oc, ec):
            stat["class-disagree"] += 1
            dis.append((t, w, key, oc, ec))
        else:
            stat["class-agree" if oc and ec else "class-unknown"] += 1

print(f"KTU {TABLET}" + (f" cols {sorted(COLS)}" if COLS else ""))
for k, v in sorted(stat.items()):
    print(f"  {v:5d}  {k}")
print(f"\n=== class disagreements ({len(dis)}) ===")
for t, w, key, oc, ec in dis:
    seeded = "SEED" if t["cmt"].startswith("SEEDED") else "curated"
    print(f"  {t['id']} {key[0]}:{key[1]:<3d} {t['surf']:12s} [{seeded:7s}] "
          f"ours={oc:5s} {t['pos'][:26]:28s} | EUPT={ec:5s} {w['morph'][:30]:32s} lemma={w['lemma']}")
