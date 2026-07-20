#!/usr/bin/env python3
"""Compare our reviewed morphological parsing (reviewed/KTU 1.N.tsv) against the
EUPT (Göttingen) edition, per token, for KTU 1.1-1.6 — on the FULL morphology
(POS, verb stem, conjugation/form, voice, person, gender, number, case, status,
pronominal/object suffix, enclitic), not just the POS tag.

For every aligned token it parses both sides' tags into a feature record and asks,
per feature and overall: is EUPT's value present among the options we list? Reports
absolute + % agreement overall and per feature, and a table of every token where
EUPT's full parse is not covered by any of our options (with the differing
features named).

Paths: reviewed files are repo-relative (auto-detected). The EUPT mirror is
external; set EUPT_DIR (default: $DULAT_APP_DATA/EUPT). No hardcoded user paths.

Usage:  EUPT_DIR=/path/to/EUPT  python agent/scripts/compare_eupt.py [1.1 1.2 ...]
"""
import os, re, sys, html, collections, unicodedata
from difflib import SequenceMatcher

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EUPT_DIR = os.environ.get("EUPT_DIR") or os.path.join(
    os.environ.get("DULAT_APP_DATA", os.path.join(os.path.expanduser("~"),
                   "projects/dulat/app/data")), "EUPT")

# ---- consonantal skeleton (for alignment) --------------------------------
# Ugaritic is consonantal: a/i/u are the three ALEPH signs (= ʔ), not vowels.
# EUPT is vocalized: aleph is written ˀ and a/i/u/e/o are real vowels. Gemination
# (doubled in EUPT) is collapsed on both sides.
def _dedup(s):
    return re.sub(r"(.)\1+", r"\1", s)
def _is_vowel(c):
    # accented Latin vowels (â/ā/á/ê/î/ô/û/…) decompose to an a/e/i/o/u base;
    # caron/dot consonants (š/ḥ/ṯ/ṣ/ḏ/ġ/ẓ/ṭ) decompose to consonant bases, so
    # this removes real vowels only, never a consonant distinction.
    return unicodedata.normalize("NFKD", c)[0].lower() in "aeiou"
def skel_ours(s):
    s = re.sub(r"[\[\]⸢⸣<>()?.\-\s]", "", s).replace("ˤ", "ʕ")
    return _dedup(re.sub(r"[aiu]", "ʔ", s))
def skel_eupt(s):
    # EUPT is vocalized; strip editorial marks (/ ! x, brackets) and the anceps
    # vowel placeholder v/V (Ugaritic has no /v/), normalize aleph/ayin, lowercase
    # (EUPT uppercases names/emphatics), drop all vowels + digits.
    s = re.sub(r"[\[\]⸢⸣<>()?.\-\s/!xvV]", "", s)
    s = s.replace("ˀ", "ʔ").replace("ˁ", "ʕ").replace("ʼ", "ʔ").lower()
    return _dedup("".join(c for c in s if not _is_vowel(c) and not c.isdigit()))

# ---- feature schema ------------------------------------------------------
DIMS = ["pos", "stem", "form", "voice", "pers", "gen", "num", "case",
        "state", "suf", "encl"]
def _empty():
    return {d: None for d in DIMS}

# coarse POS classes and compatibility (proper/common noun; function words)
def our_pos(h):
    p = h.lower()
    # name codes are UPPERCASE (DN/PN/TN/GN) and lead the POS; "pn." lowercase is
    # a pronoun ("pers. pn.", "pn. interr.") — match name case-sensitively.
    if re.match(r"(DN|PN|TN|GN)\b", h): return "name"
    if "pron" in p or "pers." in p or "rel" in p or "det" in p or re.search(r"\bpn\b", p): return "pron"
    if re.search(r"\bn\.", p): return "noun"
    if "vb" in p: return "verb"
    if "adj" in p: return "adj"
    if "num" in p: return "num"
    if "prep" in p: return "prep"
    if "conj" in p: return "conj"
    return "ptcl"
_PGRP = [{"noun", "name", "adj"}, {"prep", "conj", "pron", "ptcl"}]
def pos_compat(a, b):
    if a == b: return True
    return any(a in g and b in g for g in _PGRP)
def case_compat(e, o):          # e = EUPT case, o = ours
    if e == o: return True
    if e == "obl": return o in ("gen", "acc")
    if e in ("lok", "term"): return o in ("acc", "gen")
    if e == "vok": return o == "nom"
    return False

# ---- EUPT morph -> features ----------------------------------------------
_STEM_RE = re.compile(r"^\s*(gp|dp|gt|dt|št|šp|lp|td|tl|g|d|š|n)\s*[-.]")
_STEM_NORM = {"gp": "G", "dp": "D", "šp": "Š", "lp": "L", "g": "G", "d": "D",
              "š": "Š", "n": "N", "gt": "Gt", "dt": "Dt", "št": "Št",
              "td": "tD", "tl": "tL"}
def eupt_class(m):
    ml = m.strip().lower()
    if not ml or ml.replace("?", "") == "" or ml.startswith("falsche zeile"):
        return "?"
    if (_STEM_RE.match(ml) or any(k in ml for k in
            ("pk", "-sk", ".sk", " sk", "imp", "inf", "ptz", "verbalsubst"))):
        return "verb"
    if "zahl" in ml or ml.startswith("num"): return "num"
    if ml.startswith("adj"): return "adj"
    if ml.startswith("präp") or ml.startswith("prep"): return "prep"
    if ml.startswith("konj") or ml.startswith("subj"): return "conj"
    if re.match(r"(gn|pn|on|tn|dn)\b", ml) or "nom.prop" in ml or ml.startswith("npm"):
        return "name"
    if "pron" in ml or ml.startswith("dem.") or "determinativ" in ml: return "pron"
    if (ml.startswith("neg") or ml.startswith("adv") or "part" in ml
            or "functor" in ml or "energ" in ml or ml.startswith("interj")
            or "interr.adv" in ml): return "ptcl"
    if (re.match(r"(nom|gen|genl|akk|obl|lok|term|vok|abs)\.?", ml)
            or ml.startswith("*") or "obl." in ml or "adv.akk" in ml): return "noun"
    return "?"

def eupt_features(m):
    F = _empty()
    ml = m.lower()
    F["pos"] = eupt_class(m)
    if F["pos"] == "verb":
        sm = _STEM_RE.match(ml)
        if sm:
            F["stem"] = _STEM_NORM.get(sm.group(1), sm.group(1).upper())
            if sm.group(1) in ("gp", "dp", "šp", "lp"): F["voice"] = "pass"
        fm = re.search(r"\b(sk|pkke|pkk|pkl|pk|imp|inf|verbalsubst|ptz)\b", ml)
        if fm:
            F["form"] = {"sk": "suffc", "pk": "prefc", "pkk": "prefc",
                         "pkl": "prefc", "pkke": "prefc", "imp": "impv",
                         "inf": "inf", "ptz": "ptcpl", "verbalsubst": "inf"}[fm.group(1)]
        if "pass" in ml or F["voice"] == "pass": F["voice"] = "pass"
        elif "akt" in ml or F["voice"] is None: F["voice"] = "act"
    cm = re.search(r"\b(nom|gen|genl|akk|obl|lok|term|vok)\b", ml)
    if cm: F["case"] = {"nom": "nom", "gen": "gen", "genl": "gen", "akk": "acc",
                        "obl": "obl", "lok": "lok", "term": "term",
                        "vok": "nom"}[cm.group(1)]
    if "st.cs" in ml: F["state"] = "cstr"
    head = re.split(r"\+\s*(?:poss\.?suff|pron\.?suff|os|ep|energ)", ml)[0]
    pm = re.search(r"\b([123])\.([mfc])\.(sg|du|pl)", head)
    if pm: F["pers"], F["gen"], F["num"] = pm.groups()
    else:
        gm = re.search(r"\b([mfc])\.(sg|du|pl)", head)
        if gm: F["gen"], F["num"] = gm.groups()
    su = re.search(r"\+\s*(?:poss\.?suff\.?|pron\.?suff\.?|os)\s*([123])\.([mfc])\.(sg|du|pl)", ml)
    if su: F["suf"] = su.groups()
    if re.search(r"\+\s*ep\b|enkl|energ", ml): F["encl"] = "y"
    return F

# ---- our POS -> features -------------------------------------------------
_OUR_STEM = {"g": "G", "gt": "Gt", "gp": "G", "d": "D", "dt": "Dt", "š": "Š",
             "št": "Št", "n": "N", "l": "L", "r": "R"}
def our_features(analysis, pos):
    F = _empty()
    parts = re.split(r"\s*\+\s*", pos)
    head = parts[0]; hl = head.lower()
    F["pos"] = our_pos(head)
    if F["pos"] == "verb":
        sm = re.search(r"\bvb\s+([a-zšḫṯ]+)", hl)
        if sm:
            st = sm.group(1)
            if "pass" in st: F["voice"] = "pass"; st = st.replace("pass", "")
            F["stem"] = _OUR_STEM.get(st, st.capitalize() or None)
        if "act. ptcpl" in hl or "act.ptcpl" in hl:
            F["form"], F["voice"] = "ptcpl", "act"
        elif "pass. ptcpl" in hl:
            F["form"], F["voice"] = "ptcpl", "pass"
        else:
            fm = re.search(r"\b(suffc|prefc|impv|inf|ptcpl)\b", hl)
            if fm: F["form"] = fm.group(1)
        if F["voice"] is None: F["voice"] = "act"
    pm = re.search(r"\b([123])\s+([cmf])\.\s*(sg|du|pl)", hl)
    if pm: F["pers"], F["gen"], F["num"] = pm.groups()
    else:
        gm = re.search(r"\b([cmf])\.\s*(sg|du|pl)", hl)
        if gm: F["gen"], F["num"] = gm.groups()
        else:
            nm = re.search(r"\b(sg|du|pl)\b", hl)
            if nm: F["num"] = nm.group(1)
    cm = re.search(r"\b(nom|gen|acc)\b", hl)
    if cm: F["case"] = cm.group(1)
    if "cstr" in hl: F["state"] = "cstr"
    elif "abs" in hl: F["state"] = "abs"
    for pt in parts[1:]:
        pl = pt.lower()
        sm = re.search(r"([123])\s+([cmf])\.\s*(sg|du|pl)\.?\s*suff", pl)
        if sm: F["suf"] = sm.groups()
        if "encl" in pl or "energic" in pl: F["encl"] = "y"
    # enclitic is authoritatively marked in the analysis (~m/~n/~nn/~y)
    if F["encl"] is None and re.search(r"~[mny]", analysis):
        F["encl"] = "y"
    return F

def conflicts(e, o):
    """dims where EUPT (e) and one of our options (o) both specify and disagree."""
    c = set()
    for d in DIMS:
        ev, ov = e[d], o[d]
        if ev is None or ov is None:
            continue
        if d == "pos":
            if not pos_compat(ev, ov): c.add(d)
        elif d == "case":
            if not case_compat(ev, ov): c.add(d)
        elif ev != ov:
            c.add(d)
    return c

# ---- parsers (EUPT philology, reviewed TSV) ------------------------------
def eupt_tokens(tab):
    h = open(os.path.join(EUPT_DIR, "html", f"KTU_{tab}_philology.html"),
             encoding="utf-8").read()
    def clean(s):
        s = re.sub(r"<[^>]+>", "", s); s = html.unescape(s)
        return re.sub(r"\s+", " ", s).strip()
    marks = [(m.start(), "lb", m.group(0)) for m in
             re.finditer(r'<span class="lb item"[^>]*>.*?</span>', h, re.S)]
    marks += [(m.start(), "w", None) for m in
              re.finditer(r'<span class="word_container">', h)]
    marks.sort()
    order, seen, line = [], {}, ""
    for idx, (pos, kind, raw) in enumerate(marks):
        if kind == "lb":
            t = clean(raw)
            if re.match(r"^[ivx]+ \d+[ab]?$", t): line = t
            continue
        chunk = h[pos:marks[idx + 1][0] if idx + 1 < len(marks) else len(h)]
        cm = re.search(r'data-corresp="([^"]*)"', chunk)
        corr = cm.group(1) if cm else None
        wm = re.search(r'<label class="body"[^>]*>(.*?)</label>', chunk, re.S)
        translit = clean(wm.group(1)) if wm else ""
        mo = re.search(r'<span class="morph">(.*?)</span>', chunk, re.S)
        morph = clean(mo.group(1)) if mo else ""
        le = re.search(r'<span class="lem">(.*?)</span>', chunk, re.S)
        lemma = clean(le.group(1)).replace("lemma:", "") if le else ""
        readings = [x.strip() for x in morph.split(" / ") if x.strip()] or [""]
        key = corr or f"_{pos}"
        if key not in seen:
            seen[key] = {"line": line, "translit": translit,
                         "skel": skel_eupt(translit), "readings": [], "lemma": lemma}
            order.append(seen[key])
        for r in readings:
            if r not in seen[key]["readings"]:
                seen[key]["readings"].append(r)
        if not seen[key]["skel"]:
            seen[key]["skel"] = skel_eupt(translit)
    return [t for t in order if t["skel"]]

def reviewed_tokens(tab):
    toks, cur, ref = [], None, ""
    for l in open(os.path.join(REPO, f"reviewed/KTU {tab}.tsv"), encoding="utf-8"):
        l = l.rstrip("\n")
        if l.startswith("#"):
            mm = re.search(r"KTU \S+ (\S+)", l)
            ref = mm.group(1) if mm else ref
            continue
        if l.startswith("id\t"):
            continue
        f = l.split("\t")
        if len(f) < 8 or not f[0].isdigit():
            continue
        if cur is None or cur["id"] != f[0]:
            cur = {"id": f[0], "ref": ref, "surface": f[1],
                   "skel": skel_ours(f[1]), "options": []}
            toks.append(cur)
        cur["options"].append((f[3], f[4], f[5]))
    return toks

def align(tab):
    E, O = eupt_tokens(tab), reviewed_tokens(tab)
    sm = SequenceMatcher(a=[e["skel"] for e in E], b=[o["skel"] for o in O],
                         autojunk=False)
    pairs, oe, oo = [], 0, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            pairs += [(E[i1 + k], O[j1 + k]) for k in range(i2 - i1)]
        else:
            oe += i2 - i1; oo += j2 - j1
    return pairs, oe, oo, len(E), len(O)

# ---- run -----------------------------------------------------------------
def run(tabs):
    tot = collections.Counter()
    feat = {d: collections.Counter() for d in DIMS}  # eupt_set/our_set/agree
    mism = []
    align_stats = {}
    for tab in tabs:
        pairs, oe, oo, ne, no = align(tab)
        align_stats[tab] = (len(pairs), oe, oo, ne, no)
        for e, o in pairs:
            broken = ("x" in o["surface"]) or all(
                op[2] in ("", "?") for op in o["options"])
            E = eupt_features(e["readings"][0]) if e["readings"] else _empty()
            if broken or E["pos"] in (None, "?"):
                tot["skipped"] += 1
                continue
            tot["compared"] += 1
            opts = [our_features(op[0], op[2]) for op in o["options"]]

            def covered(d):  # does ANY of our options carry EUPT's value for d?
                return any(op[d] is not None and (
                    (d == "pos" and pos_compat(E[d], op[d])) or
                    (d == "case" and case_compat(E[d], op[d])) or
                    (d not in ("pos", "case") and op[d] == E[d])) for op in opts)

            # per-feature agreement (any option matches EUPT's value)
            for d in DIMS:
                if E[d] is None:
                    continue
                feat[d]["eupt"] += 1
                if any(op[d] is not None for op in opts):
                    feat[d]["our"] += 1
                if covered(d):
                    feat[d]["agree"] += 1
            # token-level gap = features where we ADDRESS the feature (some option
            # specifies it) but NO option matches EUPT's value. A feature one
            # option supplies is not a gap even if a different option conflicts on
            # it; a feature we simply don't annotate (all options None) is silence,
            # not a disagreement, so it is not reported.
            uncovered = {d for d in DIMS if E[d] is not None
                         and any(op[d] is not None for op in opts)
                         and not covered(d)}
            if not uncovered:
                tot["full_cover"] += 1
            else:
                tot["gap"] += 1
                mism.append((tab, e, o, E, opts, uncovered))
    return tot, feat, mism, align_stats

def fv(d):  # display name
    return {"pos": "POS", "stem": "stem", "form": "conjugation/form",
            "voice": "voice", "pers": "person", "gen": "gender",
            "num": "number", "case": "case", "state": "status (cstr/abs)",
            "suf": "pron. suffix", "encl": "enclitic"}[d]

def main():
    tabs = sys.argv[1:] or ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"]
    if not os.path.isdir(os.path.join(EUPT_DIR, "html")):
        sys.exit(f"EUPT_DIR not found: {EUPT_DIR} (set EUPT_DIR env var)")
    tot, feat, mism, align_stats = run(tabs)
    W = "=" * 80
    print(W + f"\nEUPT vs our reviewed FULL-morphology comparison — KTU "
          + ", ".join(tabs) + "\n" + W)
    print("\nAlignment (by consonantal skeleton, aleph-aware):")
    print(f"  {'tablet':7}{'EUPT':>7}{'ours':>7}{'aligned':>9}"
          f"{'EUPT-only':>11}{'ours-only':>11}")
    for t in tabs:
        a, oe, oo, ne, no = align_stats[t]
        print(f"  {t:7}{ne:7}{no:7}{a:9}{oe:11}{oo:11}")
    ta = sum(a[0] for a in align_stats.values())
    to = sum(a[4] for a in align_stats.values())
    c = tot["compared"] or 1
    print(f"\nComparable tokens (aligned, both parsed): {tot['compared']}   "
          f"(skipped {tot['skipped']}; alignment covers {ta}/{to} of ours)")
    print(f"  EUPT's FULL parse covered by some option : {tot['full_cover']:5}  "
          f"({100*tot['full_cover']/c:5.1f}%)")
    print(f"  NOT fully covered (>=1 feature differs)  : {tot['gap']:5}  "
          f"({100*tot['gap']/c:5.1f}%)")
    print("\nPer-feature agreement (of tokens where EUPT specifies the feature):")
    print(f"  {'feature':20}{'EUPT-has':>9}{'we-have':>9}{'agree':>7}{'agree%':>8}")
    for d in DIMS:
        eh = feat[d]["eupt"]
        if not eh:
            continue
        print(f"  {fv(d):20}{eh:9}{feat[d]['our']:9}{feat[d]['agree']:7}"
              f"{100*feat[d]['agree']/eh:7.1f}%")

    out_tsv = os.path.join(REPO, "agent/reports/eupt_vs_reviewed_gaps.tsv")
    os.makedirs(os.path.dirname(out_tsv), exist_ok=True)
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("tablet\tref\ttoken_id\tsurface\tdiffering_features\t"
                 "eupt_translit\teupt_morph\teupt_lemma\tour_options\n")
        def ourvals(opts_f, d):  # distinct values our options carry for dim d
            return "/".join(sorted({str(op[d]) for op in opts_f if op[d] is not None})) or "None"
        for tab, e, o, E, opts_f, unc in sorted(mism, key=lambda g: (g[0], int(g[2]['id']))):
            diffs = ";".join(f"{fv(d)}:EUPT={E[d]}/ours={ourvals(opts_f, d)}"
                             for d in DIMS if d in unc)
            opts = " | ".join(f"{op[0]}={op[2]}" for op in o["options"])
            fh.write(f"{tab}\t{o['ref']}\t{o['id']}\t{o['surface']}\t{diffs}\t"
                     f"{e['translit']}\t{e['readings'][0]}\t{e['lemma']}\t{opts}\n")

    dimc = collections.Counter(d for _, _, _, _, _, unc in mism for d in unc)
    print(f"\n{W}\nGAPS — EUPT's full parse not covered by any option "
          f"({len(mism)} tokens).  Differing-feature frequency:\n{W}")
    for d in DIMS:
        if dimc[d]:
            print(f"  {fv(d):20} {dimc[d]}")
    print(f"\nFull list -> {os.path.relpath(out_tsv, REPO)}   "
          f"(showing first 60; each line: KTU ref, id, surface, diffs)")
    for tab, e, o, E, opts_f, unc in sorted(mism, key=lambda g: (g[0], int(g[2]['id'])))[:60]:
        diffs = " ".join(f"{d}:{E[d]}≠{ourvals(opts_f, d)}" for d in DIMS if d in unc)
        print(f"  {tab+' '+o['ref']:11} {o['id']:7} {o['surface'][:10]:10} "
              f"{e['translit'][:12]:12} [{e['readings'][0][:34]:34}]  {diffs}")

if __name__ == "__main__":
    main()
