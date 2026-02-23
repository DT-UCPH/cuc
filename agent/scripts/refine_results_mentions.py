#!/usr/bin/env python3
"""
Refine structured morphology TSV files using:
- DULAT forms/entries,
- reverse mention indices (dulat_reverse_refs + ktu_to_dulat),
- conservative clitic suffix splitting.

Designed for results/*.tsv in 7-column format.
"""

from __future__ import annotations

import argparse
import html
import math
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

SEPARATOR_RE = re.compile(r"^#-+\s*KTU\s+(\d+\.\d+)\s+([IVX]+):(\d+)\s*$", re.IGNORECASE)

LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)

ANALYSIS_NORMALIZE = str.maketrans(
    {
        "ʿ": "ˤ",
        "ʕ": "ˤ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)

POS_LABEL_NORMALIZATION = {
    "det. / rel. functor": "det. or rel. functor",
    "subordinating / completive functor": "Subordinating or completive functor",
    "emph./det. encl. morph.": "emph. or det. encl. morph.",
    "adv./emph. functor": "adv. or emph. functor",
    "adv./prep.": "adv. or prep.",
    "adj./n.": "adj. or n.",
    "adj. /n.": "adj. or n.",
    "n./adj. (?)": "n. or adj. (?)",
    "pn/dn": "PN or DN",
    "pn/gn": "PN or GN",
    "pn/tn (?)": "PN or TN (?)",
    "dn/tn": "DN or TN",
    "gn/tn": "GN or TN",
    "tn/toponymic element": "TN or toponymic element",
}

LETTER_RE = re.compile(r"[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ]")


@dataclass(frozen=True)
class Entry:
    entry_id: int
    lemma: str
    hom: str
    pos: str
    gloss: str
    wiki_tr: str


@dataclass
class Variant:
    entries: Tuple[Entry, ...]
    base_surface: str
    score: int = 0


# ------------------ helpers ------------------


def normalize_lookup(s: str) -> str:
    return (s or "").translate(LOOKUP_NORMALIZE).strip()


def normalize_analysis(s: str) -> str:
    return (s or "").translate(ANALYSIS_NORMALIZE).strip()


def strip_html(s: str) -> str:
    text = html.unescape(s or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compact_gloss(s: str) -> str:
    g = strip_html(s)
    if not g:
        return ""
    g = g.replace("\n", " ")
    g = re.sub(r"\s+", " ", g)
    g = g.replace(";", ",")
    g = g.replace('"', "")
    g = re.sub(r"^\s*\d+\)\s*", "", g)
    g = re.sub(r"^\s*[a-z]\)\s*", "", g)
    # Keep first concise segment.
    g = g.split(",", 1)[0]
    g = g.strip(" ,;")
    # keep compact first chunk when automated extraction is noisy
    if len(g) > 110:
        g = g[:110].rsplit(" ", 1)[0].strip(" ,;")
    return g


def canon_ref(r: str) -> str:
    t = (r or "").strip()
    t = re.sub(r"\s+", " ", t)
    t = t.replace("KTU ", "CAT ")
    t = t.replace("CATCAT", "CAT")
    return t


def parse_separator_ref(line: str) -> Optional[str]:
    m = SEPARATOR_RE.match(line.strip())
    if not m:
        return None
    tablet, col, ln = m.group(1), m.group(2).upper(), m.group(3)
    return f"CAT {tablet} {col}:{ln}"


def tablet_id_from_ref(ref: str) -> str:
    m = re.search(r"CAT\s+(\d+\.\d+)", ref or "")
    return m.group(1) if m else ""


def tablet_family(tablet_id: str) -> str:
    return (tablet_id or "").split(".", 1)[0]


def parse_optional_hom(lemma: str, hom: str) -> Tuple[str, str]:
    lm = (lemma or "").strip()
    hm = (hom or "").strip()
    if lm and not hm:
        m = re.match(r"^(.*)\s+\(([IV]+)\)$", lm)
        if m:
            return m.group(1).strip(), m.group(2)
    return lm, hm


def entry_label(e: Entry) -> str:
    lemma = (e.lemma or "").strip()
    if not (lemma.startswith("/") and lemma.endswith("/")) and "/" in lemma:
        first = lemma.split("/", 1)[0].strip()
        # Some DULAT headwords encode orthographic alternatives like
        # ỉ/ủšḫry. Keeping only the first short fragment would destroy
        # lexical identity (ỉ), so preserve the full slash lemma.
        if len(extract_letters(first)) > 2:
            lemma = first
    if e.hom:
        return f"{lemma} ({e.hom})"
    return lemma


def normalize_pos_label(pos: str) -> str:
    tok = re.sub(r"\s+", " ", (pos or "").strip())
    if not tok:
        return ""
    return POS_LABEL_NORMALIZATION.get(tok.lower(), tok)


def pos_token(e: Entry) -> str:
    parts = [normalize_pos_label(p.strip()) for p in (e.pos or "").split(",") if p.strip()]
    if not parts:
        return ""
    # In col5 one morpheme slot can keep alternatives with '/'
    return "/".join(parts)


def is_verb_pos(pos: str) -> bool:
    return "vb" in (pos or "").lower()


def is_nominal_pos(pos: str) -> bool:
    p = (pos or "").lower()
    return any(k in p for k in ("n.", "adj", "dn", "pn", "tn", "gn", "mn", "num", "element"))


def extract_letters(text: str) -> str:
    return "".join(ch for ch in (text or "") if LETTER_RE.match(ch))


def lemma_to_letters(lemma: str, fallback: str = "") -> str:
    lm = (lemma or "").strip()
    if not lm:
        return normalize_analysis(extract_letters(fallback))

    if lm.startswith("/") and lm.endswith("/"):
        body = lm[1:-1]
        body = body.split("/", 1)[0]
        body = re.sub(r"\([^)]*\)", "", body)
        body = body.replace("-", "")
        letters = extract_letters(body)
        if letters:
            return normalize_analysis(letters)

    # non-root lemma
    body = lm.split("/", 1)[0]
    body = re.sub(r"\([^)]*\)", "", body)
    letters = extract_letters(body)
    if letters:
        return normalize_analysis(letters)
    return normalize_analysis(extract_letters(fallback))


def stem_marker_from_morph(morph_values: Sequence[str]) -> str:
    merged = " | ".join(morph_values or [])
    if not merged:
        return ""
    if "Št" in merged:
        return "]š]]t]"
    if "Gt" in merged:
        return "]t]"
    if "Š" in merged:
        return "]š]"
    return ""


def analysis_for_entry(surface: str, e: Entry, morph_values: Optional[Sequence[str]] = None) -> str:
    s = normalize_analysis(surface)
    hom = f"({e.hom})" if e.hom else ""
    stem_marker = stem_marker_from_morph(morph_values or [])

    if is_verb_pos(e.pos):
        stem = lemma_to_letters(e.lemma, fallback=s)
        if stem_marker == "]t]" and stem:
            # Xt stems place the t infix after the first root radical.
            stem = stem[0] + "]t]" + stem[1:]
            stem_marker = ""
        if s and s[0] in {"y", "t", "a", "n", "i", "u"} and len(s) >= len(stem) + 1:
            return f"!{s[0]}!{stem_marker}{stem}{hom}["
        return f"{stem_marker}{stem}{hom}["

    lex = lemma_to_letters(e.lemma, fallback=s)
    if (
        "/" in (e.lemma or "")
        and not ((e.lemma or "").startswith("/") and (e.lemma or "").endswith("/"))
        and len(lex) <= 2
        and len(s) >= 4
    ):
        # Slash-variant lemmas like ỉ/ủšḫry can collapse to a one-letter
        # fragment if we keep only the first variant. For long surfaces,
        # prefer the observed token shape.
        lex = s
    if is_nominal_pos(e.pos):
        return f"{lex}{hom}/"
    return f"{lex}{hom}"


def suffix_fragment(e: Entry) -> str:
    frag = lemma_to_letters(e.lemma.lstrip("-"), fallback=e.lemma.lstrip("-"))
    if e.hom:
        return f"{frag}({e.hom})"
    return frag


def gloss_for_entry(e: Entry, multi_slot: bool = False) -> str:
    pos_up = e.pos or ""
    if any(tag in pos_up for tag in ("DN", "PN", "TN", "GN")):
        # Prefer canonical name rendering for proper names if available.
        base = compact_gloss(e.wiki_tr) or compact_gloss(e.gloss) or entry_label(e)
    else:
        base = compact_gloss(e.gloss)
    if not base:
        base = ""
    if multi_slot:
        base = base.replace(",", " / ")
    return base


# ------------------ loading ------------------


def load_entries(
    dulat_db: Path,
) -> Tuple[
    Dict[int, Entry],
    Dict[str, List[Entry]],
    Dict[str, List[Entry]],
    Dict[str, List[Entry]],
    Dict[Tuple[str, int], Set[str]],
]:
    conn = sqlite3.connect(str(dulat_db))
    cur = conn.cursor()

    # compact gloss preference
    sense_map: Dict[int, str] = {}
    cur.execute(
        "SELECT entry_id, definition "
        "FROM senses "
        "WHERE definition IS NOT NULL AND trim(definition) != '' "
        "ORDER BY entry_id, id"
    )
    for entry_id, definition in cur.fetchall():
        if entry_id not in sense_map:
            sense_map[entry_id] = compact_gloss(definition)

    trans_map: Dict[int, str] = {}
    cur.execute(
        "SELECT entry_id, text "
        "FROM translations "
        "WHERE text IS NOT NULL AND trim(text) != '' "
        "ORDER BY entry_id, rowid"
    )
    for entry_id, text in cur.fetchall():
        if entry_id not in trans_map:
            trans_map[entry_id] = compact_gloss(text)

    cur.execute("SELECT entry_id, lemma, homonym, pos, wiki_transcription FROM entries")
    entries_by_id: Dict[int, Entry] = {}
    lemma_map: Dict[str, List[Entry]] = {}
    suffix_map: Dict[str, List[Entry]] = {}
    for entry_id, lemma, hom, pos, wiki_tr in cur.fetchall():
        lm, hm = parse_optional_hom(lemma or "", hom or "")
        e = Entry(
            entry_id=int(entry_id),
            lemma=lm,
            hom=hm,
            pos=pos or "",
            gloss=sense_map.get(entry_id) or trans_map.get(entry_id, ""),
            wiki_tr=wiki_tr or "",
        )
        entries_by_id[e.entry_id] = e
        key = normalize_lookup(lm)
        if key:
            lemma_map.setdefault(key, []).append(e)
        if lm.startswith("-"):
            suf = normalize_lookup(lm.lstrip("-"))
            if suf:
                suffix_map.setdefault(suf, []).append(e)

    forms_map: Dict[str, List[Entry]] = {}
    forms_morph: Dict[Tuple[str, int], Set[str]] = {}
    cur.execute("SELECT text, entry_id FROM forms WHERE text IS NOT NULL AND trim(text) != ''")
    for txt, entry_id in cur.fetchall():
        e = entries_by_id.get(int(entry_id))
        if not e:
            continue
        k = normalize_lookup(txt)
        if k:
            forms_map.setdefault(k, []).append(e)
    cur.execute(
        "SELECT text, entry_id, morphology FROM forms WHERE text IS NOT NULL AND trim(text) != ''"
    )
    for txt, entry_id, morph in cur.fetchall():
        k = normalize_lookup(txt)
        if not k:
            continue
        forms_morph.setdefault((k, int(entry_id)), set()).add((morph or "").strip())

    explicit_form_keys = set(forms_map.keys())

    # Conservative fallback: if an entry lemma exists in DULAT but no
    # corresponding form row exists for that exact token, index the lemma
    # itself so unresolved rows are still populated from lexical metadata.
    fallback_by_key: Dict[str, List[Entry]] = {}
    for entry in entries_by_id.values():
        lemma_key = normalize_lookup(entry.lemma)
        if not lemma_key or " " in lemma_key:
            continue
        if lemma_key in explicit_form_keys:
            continue
        fallback_by_key.setdefault(lemma_key, []).append(entry)

    for lemma_key, candidates in fallback_by_key.items():
        forms_map.setdefault(lemma_key, []).extend(candidates)

    conn.close()
    return entries_by_id, forms_map, lemma_map, suffix_map, forms_morph


def load_reverse_mentions(
    dulat_db: Path, udb_db: Path
) -> Tuple[Dict[str, Set[int]], Dict[int, int], Dict[int, Set[str]], Dict[int, Dict[str, int]]]:
    out: Dict[str, Set[int]] = {}
    entry_ref_count: Counter = Counter()
    entry_tablets: Dict[int, Set[str]] = defaultdict(set)
    entry_family_count: Dict[int, Counter] = defaultdict(Counter)
    seen_pairs: Set[Tuple[str, int]] = set()

    conn = sqlite3.connect(str(dulat_db))
    cur = conn.cursor()
    cur.execute("SELECT norm_ref, entry_id FROM dulat_reverse_refs")
    for ref, entry_id in cur.fetchall():
        rk = canon_ref(ref)
        eid = int(entry_id)
        out.setdefault(rk, set()).add(eid)
        key = (rk, eid)
        if key not in seen_pairs:
            seen_pairs.add(key)
            entry_ref_count[eid] += 1
            tid = tablet_id_from_ref(rk)
            if tid:
                entry_tablets[eid].add(tid)
                fam = tablet_family(tid)
                if fam:
                    entry_family_count[eid][fam] += 1
    conn.close()

    conn = sqlite3.connect(str(udb_db))
    cur = conn.cursor()
    cur.execute("SELECT ktu_ref, entry_id FROM ktu_to_dulat")
    for ref, entry_id in cur.fetchall():
        rk = canon_ref(ref)
        eid = int(entry_id)
        out.setdefault(rk, set()).add(eid)
        key = (rk, eid)
        if key not in seen_pairs:
            seen_pairs.add(key)
            entry_ref_count[eid] += 1
            tid = tablet_id_from_ref(rk)
            if tid:
                entry_tablets[eid].add(tid)
                fam = tablet_family(tid)
                if fam:
                    entry_family_count[eid][fam] += 1
    conn.close()

    return (
        out,
        dict(entry_ref_count),
        dict(entry_tablets),
        {k: dict(v) for k, v in entry_family_count.items()},
    )


# ------------------ refinement ------------------


def score_variant(
    v: Variant,
    surface: str,
    current_ref: str,
    direct_ids: Set[int],
    mention_ids: Set[int],
    forms_morph: Dict[Tuple[str, int], Set[str]],
    entry_ref_count: Dict[int, int],
    entry_tablets: Dict[int, Set[str]],
    entry_family_count: Dict[int, Dict[str, int]],
) -> int:
    s = 0
    surf = normalize_analysis(surface)
    if len(v.entries) == 1 and v.entries[0].entry_id in direct_ids:
        s += 5
    lexical_entries = [e for e in v.entries if not e.lemma.startswith("-")]
    mh = sum(1 for e in lexical_entries if e.entry_id in mention_ids)
    s += mh * 2
    if len(v.entries) > 1:
        s += 1  # reward explicit clitic split when valid
    if lexical_entries:
        pe = lexical_entries[0]
        ltxt = lemma_to_letters(pe.lemma, fallback=surf)
        if ltxt == surf:
            s += 10
        elif surf.startswith(ltxt) or surf.endswith(ltxt):
            s += 3
        elif ltxt and ltxt[0] == surf[:1]:
            s += 1
        if is_verb_pos(pe.pos) and normalize_analysis(surface)[:1] in {
            "y",
            "t",
            "a",
            "n",
            "i",
            "u",
        }:
            s += 1
        if is_verb_pos(pe.pos) and len(surf) <= 2:
            s -= 2
        if (not is_verb_pos(pe.pos)) and len(surf) <= 2:
            s += 1
        if "→" in (pe.pos or ""):
            s -= 2
        if not (pe.pos or "").strip():
            s -= 1

        # Use DULAT form morphology (for this exact surface) as generic tie-breaker.
        fm = " | ".join(
            sorted(forms_morph.get((normalize_lookup(surface), pe.entry_id), set()))
        ).lower()
        if fm:
            ends_pron_suffix = bool(re.search(r"(y|k|h|hm|hn|km|kn|n)$", normalize_lookup(surface)))
            if "pn." in fm:
                s += 5 if ends_pron_suffix else 3
            if "suff" in fm:
                s += 2
            if "sg." in fm and "pn." not in fm and ends_pron_suffix:
                s -= 2
            if "prep" in (pe.pos or "").lower() and "pn." in fm:
                s += 6

        # Global attestation prior: frequent entry_id is preferred in unresolved ties.
        ref_n = entry_ref_count.get(pe.entry_id, 0)
        if ref_n > 0:
            s += min(8, int(math.log10(ref_n + 1) * 4))
        if ref_n <= 2:
            s -= 2

        # Tablet-distribution prior: penalize narrow PN/TN/DN entries
        # outside their attested tablet set.
        cur_tab = tablet_id_from_ref(current_ref)
        cur_family = tablet_family(cur_tab)
        tabs = entry_tablets.get(pe.entry_id, set())
        fam_counts = entry_family_count.get(pe.entry_id, {})
        if cur_tab and tabs and cur_tab not in tabs:
            pos_raw = pe.pos or ""
            if "PN" in pos_raw and len(tabs) <= 2:
                s -= 6
            elif ("TN" in pos_raw or "DN" in pos_raw) and len(tabs) <= 2:
                s -= 3
        if cur_family and fam_counts:
            total = sum(fam_counts.values())
            top_family = max(fam_counts, key=fam_counts.get)
            top_ratio = fam_counts[top_family] / total if total else 0.0
            if cur_family not in fam_counts:
                pos_raw = pe.pos or ""
                if ("PN" in pos_raw or "TN" in pos_raw) and total >= 6 and top_ratio >= 0.8:
                    s -= 8
                elif "DN" in pos_raw and total >= 6 and top_ratio >= 0.9:
                    s -= 4
            elif cur_family == top_family and fam_counts[top_family] >= 5:
                s += 1
    return s


def dedupe_entries(entries: Iterable[Entry]) -> List[Entry]:
    seen = set()
    out = []
    for e in entries:
        if e.entry_id in seen:
            continue
        seen.add(e.entry_id)
        out.append(e)
    return out


def build_variants(
    surface: str,
    current_ref: str,
    forms_map: Dict[str, List[Entry]],
    suffix_map: Dict[str, List[Entry]],
    forms_morph: Dict[Tuple[str, int], Set[str]],
    mention_ids: Set[int],
    entry_ref_count: Dict[int, int],
    entry_tablets: Dict[int, Set[str]],
    entry_family_count: Dict[int, Dict[str, int]],
    max_variants: int = 3,
) -> List[Variant]:
    s_norm = normalize_lookup(surface)
    direct_all = dedupe_entries(forms_map.get(s_norm, []))
    direct_pref = [e for e in direct_all if (e.pos or "").strip() and (e.pos or "").strip() != "→"]
    direct = direct_pref if direct_pref else direct_all
    direct_ids = {e.entry_id for e in direct}

    variants: List[Variant] = [Variant((e,), surface) for e in direct]

    # Conservative suffix splitting, only when direct form mapping failed.
    if not direct:
        suffixes = sorted(suffix_map.keys(), key=len, reverse=True)
        for suf in suffixes:
            if not s_norm.endswith(suf) or len(s_norm) <= len(suf):
                continue
            base_norm = s_norm[: -len(suf)]
            base_all = dedupe_entries(forms_map.get(base_norm, []))
            base_pref = [
                e for e in base_all if (e.pos or "").strip() and (e.pos or "").strip() != "→"
            ]
            base_entries = base_pref if base_pref else base_all
            if not base_entries:
                continue
            suffix_all = dedupe_entries(suffix_map.get(suf, []))
            suffix_pref = [
                e for e in suffix_all if (e.pos or "").strip() and (e.pos or "").strip() != "→"
            ]
            suffix_entries = suffix_pref if suffix_pref else suffix_all
            if not suffix_entries:
                continue
            # derive base surface by raw trimming (best effort)
            base_surface = surface[: max(1, len(surface) - len(suf))]
            for be in base_entries[:4]:
                for se in suffix_entries[:3]:
                    variants.append(Variant((be, se), base_surface))

    if not variants:
        return []

    # reverse mentions are used as soft ranking signal (score boost), not hard filter.

    # dedupe by entry_id signature + base surface
    uniq: Dict[Tuple[Tuple[int, ...], str], Variant] = {}
    for v in variants:
        sig = (tuple(e.entry_id for e in v.entries), v.base_surface)
        if sig not in uniq:
            uniq[sig] = v
    variants = list(uniq.values())

    for v in variants:
        v.score = score_variant(
            v,
            surface,
            current_ref,
            direct_ids,
            mention_ids,
            forms_morph,
            entry_ref_count,
            entry_tablets,
            entry_family_count,
        )

    # If one candidate is vastly more attested globally than alternatives, prefer it.
    single_entry_variants = [v for v in variants if len(v.entries) == 1]
    if len(single_entry_variants) >= 2:
        counts = sorted(
            (
                (entry_ref_count.get(v.entries[0].entry_id, 0), v.entries[0].entry_id)
                for v in single_entry_variants
            ),
            reverse=True,
        )
        top_n, top_id = counts[0]
        second_n = counts[1][0]
        if top_n >= 20 and (second_n == 0 or top_n >= 10 * max(1, second_n)):
            for v in variants:
                if len(v.entries) == 1 and v.entries[0].entry_id == top_id:
                    v.score += 4
                elif len(v.entries) == 1:
                    v.score -= 2

    variants.sort(
        key=lambda v: (
            -v.score,
            len(v.entries),
            tuple(entry_label(e) for e in v.entries),
        )
    )
    # Collapse to one variant when evidence is strongly skewed.
    if len(variants) > 1 and (variants[0].score - variants[1].score) >= 6:
        return [variants[0]]
    return variants[:max_variants]


def render_variant(
    surface: str, v: Variant, forms_morph: Dict[Tuple[str, int], Set[str]]
) -> Tuple[str, str, str, str]:
    entries = list(v.entries)
    if len(entries) == 1:
        e = entries[0]
        mv = sorted(forms_morph.get((normalize_lookup(surface), e.entry_id), set()))
        a = analysis_for_entry(surface, e, morph_values=mv)
        d = entry_label(e)
        p = pos_token(e)
        g = gloss_for_entry(e, multi_slot=False)
        return a, d, p, g

    base, suf = entries[0], entries[1]
    mv = sorted(forms_morph.get((normalize_lookup(v.base_surface), base.entry_id), set()))
    a = f"{analysis_for_entry(v.base_surface, base, morph_values=mv)}+{suffix_fragment(suf)}"
    d = f"{entry_label(base)},{entry_label(suf)}"
    p = f"{pos_token(base)},{pos_token(suf)}"
    g = f"{gloss_for_entry(base, multi_slot=True)},{gloss_for_entry(suf, multi_slot=True)}"
    return a, d, p, g


def refine_file(
    path: Path,
    out_path: Path,
    forms_map: Dict[str, List[Entry]],
    suffix_map: Dict[str, List[Entry]],
    forms_morph: Dict[Tuple[str, int], Set[str]],
    reverse_mentions: Dict[str, Set[int]],
    entry_ref_count: Dict[int, int],
    entry_tablets: Dict[int, Set[str]],
    entry_family_count: Dict[int, Dict[str, int]],
    only_not_found: bool = False,
) -> Tuple[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    out_lines: List[str] = []

    current_ref = ""
    rows = 0
    changed = 0

    for raw in lines:
        ref = parse_separator_ref(raw)
        if ref:
            current_ref = canon_ref(ref)
            out_lines.append(raw)
            continue

        if not raw.strip() or raw.lstrip().startswith("#"):
            out_lines.append(raw)
            continue

        if only_not_found and "DULAT: NOT FOUND" not in raw:
            out_lines.append(raw)
            rows += 1
            continue

        comment = ""
        core = raw
        if "#" in raw:
            core, comment = raw.split("#", 1)
            core = core.rstrip()
            comment = comment.strip()

        parts = core.split("\t")
        while len(parts) < 7:
            parts.append("")

        line_id = parts[0].strip()
        surface = normalize_analysis(parts[1].strip())

        # preserve empty and fully broken rows
        if not surface:
            new_parts = [line_id, surface, "", "", "", "", ""]
            out_lines.append("\t".join(new_parts))
            rows += 1
            continue
        if re.fullmatch(r"[xX]+", surface):
            new_parts = [line_id, surface, surface, "", "", "", ""]
            out_lines.append("\t".join(new_parts))
            rows += 1
            continue

        mention_ids = reverse_mentions.get(current_ref, set()) if current_ref else set()
        variants = build_variants(
            surface,
            current_ref,
            forms_map,
            suffix_map,
            forms_morph,
            mention_ids,
            entry_ref_count,
            entry_tablets,
            entry_family_count,
            max_variants=3,
        )

        if not variants:
            if only_not_found:
                out_lines.append(raw)
                rows += 1
                continue
            new_parts = [line_id, surface, surface, "", "", "", "DULAT: NOT FOUND"]
        else:
            analyses: List[str] = []
            dulat_tokens: List[str] = []
            pos_tokens: List[str] = []
            gloss_tokens: List[str] = []
            for v in variants:
                a, d, p, g = render_variant(surface, v, forms_morph=forms_morph)
                analyses.append(a)
                dulat_tokens.append(d)
                pos_tokens.append(p)
                gloss_tokens.append(g)

            new_parts = [
                line_id,
                surface,
                ";".join(analyses),
                ";".join(dulat_tokens),
                ";".join(pos_tokens),
                ";".join(gloss_tokens),
                "",
            ]

        new_line = "\t".join(new_parts)
        if comment and not comment.startswith("DULAT: NOT FOUND"):
            # Keep only non-redundant human note comments.
            new_line += f" # {comment}"

        if new_line != raw:
            changed += 1
        rows += 1
        out_lines.append(new_line)

    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return rows, changed


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Refine morphology TSV using reverse mentions + clitic splitting"
    )
    ap.add_argument("files", nargs="+", help="TSV files to refine")
    ap.add_argument("--dulat-db", default="sources/dulat_cache.sqlite")
    ap.add_argument("--udb-db", default="sources/udb_cache.sqlite")
    ap.add_argument("--in-place", action="store_true", help="Rewrite files in place")
    ap.add_argument("--out-dir", default="results", help="Output dir if not --in-place")
    ap.add_argument(
        "--only-not-found",
        action="store_true",
        help="Refine only rows currently marked with DULAT: NOT FOUND",
    )
    args = ap.parse_args()

    _entries_by_id, forms_map, _lemma_map, suffix_map, forms_morph = load_entries(
        Path(args.dulat_db)
    )
    reverse_mentions, entry_ref_count, entry_tablets, entry_family_count = load_reverse_mentions(
        Path(args.dulat_db), Path(args.udb_db)
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in args.files:
        src = Path(f)
        dst = src if args.in_place else out_dir / src.name
        rows, changed = refine_file(
            src,
            dst,
            forms_map,
            suffix_map,
            forms_morph,
            reverse_mentions,
            entry_ref_count,
            entry_tablets,
            entry_family_count,
            only_not_found=args.only_not_found,
        )
        print(f"{src} -> {dst} | rows={rows} changed={changed}")


if __name__ == "__main__":
    main()
