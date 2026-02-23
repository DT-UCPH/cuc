#!/usr/bin/env python3
import argparse
import html
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# -----------------------------
# Utilities
# -----------------------------

ALEPH_NORMALIZE = str.maketrans(
    {
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
        "ʿ": "ʕ",
        "ˤ": "ʕ",
    }
)

ALEPH_NORMALIZE_UDB = str.maketrans(
    {
        "ˤ": "ʿ",
        "ʕ": "ʿ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)


def normalize_surface(s: str) -> str:
    return s.translate(ALEPH_NORMALIZE)


def normalize_udb(s: str) -> str:
    return s.translate(ALEPH_NORMALIZE_UDB)


def lemma_aliases(lemma: str) -> List[str]:
    """
    Generate additional lookup aliases for lemmas with optional/alternative segments.

    DULAT conventions include:
    - /ʔ-ḫ-d(/ḏ)/ : alternative reading of the last segment (d vs ḏ)
    - /ʕ-d(-d)/   : optional added segment

    Expected aliases include:
    - /ʔ-ḫ-d/ and /ʔ-ḫ-ḏ/
    - /ʕ-d/ and /ʕ-d-d/
    """
    if not lemma:
        return []
    out = {lemma}
    queue = [lemma]
    seen = set()

    while queue:
        item = queue.pop()
        if item in seen:
            continue
        seen.add(item)
        m = re.search(r"\(([^)]*)\)", item)
        if not m:
            continue

        inner = (m.group(1) or "").strip()
        pre = item[: m.start()]
        suf = item[m.end() :]

        # Always allow the "without parenthetical" variant.
        drop = pre + suf
        if drop not in out:
            out.add(drop)
            queue.append(drop)

        if not inner:
            continue

        # Alternative reading variant, e.g. d(/ḏ) => d | ḏ (replacement of prior segment)
        if inner.startswith("/"):
            alts = [a for a in inner.split("/") if a]
            if not alts:
                continue
            sep = max(pre.rfind("-"), pre.rfind("/"))
            if sep >= 0 and sep + 1 < len(pre):
                base = pre[: sep + 1]
            else:
                base = pre
            for alt in alts:
                cand = base + alt + suf
                if cand not in out:
                    out.add(cand)
                    queue.append(cand)
            continue

        # Optional added segment, e.g. (-w:y) => (none) | -w | -y
        if inner.startswith("-"):
            payload = inner[1:]
            alts = [a for a in payload.split(":") if a] if payload else []
            for alt in alts:
                cand = pre + "-" + alt + suf
                if cand not in out:
                    out.add(cand)
                    queue.append(cand)
            continue

        # Generic parenthetical alternation/addition: (x:y) => x | y
        alts = [a for a in inner.split(":") if a]
        for alt in alts:
            cand = pre + alt + suf
            if cand not in out:
                out.add(cand)
                queue.append(cand)

    cleaned = set()
    for item in out:
        x = item
        x = re.sub(r"/{2,}", "/", x)
        x = re.sub(r"-{2,}", "-", x)
        x = x.replace("/-", "/").replace("-/", "/")
        x = x.strip()
        if x:
            cleaned.add(x)
    return sorted(cleaned)


def strip_missing(s: str) -> str:
    return re.sub(r"[xX]", "", s)


def strip_markers_simple(s: str) -> str:
    # Remove prefix/stem markers and common morphology markers
    s = re.sub(r"!.*?!", "", s)
    s = re.sub(r"\].*?\]", "", s)
    s = re.sub(r"[\[\]/=:+~]", "", s)
    s = s.replace("(", "").replace(")", "").replace("&", "")
    return s.strip()


def has_letters(s: str) -> bool:
    return re.search(r"[A-Za-zˤʔḫṣṯẓġḏḥṭš]", s) is not None


LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭš]")
ANALYSIS_SURFACE_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_CLITIC_SUFFIX_SEGMENTS = ("hm", "hn", "km", "kn", "ny", "nm", "nn", "h", "k", "n", "y")
_DECLARED_SUFFIX_NY_RE = re.compile(r",\s*-[ny](?:\s|\(|$)", flags=re.IGNORECASE)
_DECLARED_LEMMA_LETTER_RE = re.compile(r"[^A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_HOMONYM_MARKED_N_CLITIC_RE = re.compile(r"(?:\+n=?|~n=?|\[n=?|-n=?)\((?:I|II|III|IV)\)")
_OFFERING_SURFACES = {
    normalize_surface("gdlt"),
    normalize_surface("alp"),
    normalize_surface("alpm"),
    normalize_surface("šnpt"),
    normalize_surface("ʕr"),
    normalize_surface("npš"),
    normalize_surface("ššrt"),
    normalize_surface("š"),
    normalize_surface("ynt"),
}

OUT_TSV_HEADER_COLUMNS = [
    "id",
    "surface form",
    "morphological parsing",
    "dulat",
    "pos",
    "gloss",
    "comments",
]


PL_TANT_RE = re.compile(
    r"(?:\bpl\.?\s*tant\b|\bplur(?:ale)?\.?\s*tant(?:um|u)?\b)\.?\??",
    flags=re.IGNORECASE,
)


def strip_plurale_tantum_marker(text: str) -> str:
    src = text or ""
    t = PL_TANT_RE.sub("", src)
    if t == src:
        return src.strip()
    # Remove punctuation residues left after marker stripping.
    t = re.sub(r"\s*[.;,]+\s*$", "", t)
    t = re.sub(r"\s+[.;,](?=\s|$)", " ", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def has_plurale_tantum_note(text: str) -> bool:
    t = text or ""
    if "pl" not in t.lower() and "plur" not in t.lower():
        return False
    return PL_TANT_RE.search(t) is not None


def has_unprefixed_reconstructed_sequence(s: str, allow_weak_y_cluster: bool = False) -> bool:
    """
    Enforce explicit per-letter reconstruction marking:
    every reconstructed letter must be preceded by '('.

    Example:
      invalid:  š(lyṭ/
      valid:    š(l(y(ṭ/

    Exempt substitution bundles like (k&w..., where only the first
    letter is reconstructed and '&' introduces surface-only material.
    Optionally exempt weak-initial y-root prefix clusters such as "(ytn",
    "(yṯb", etc., where only initial y is reconstructed.
    """
    i = 0
    while i < len(s):
        if s[i] != "(":
            i += 1
            continue

        # Skip homonym tags like (I), (II), (III), (IV).
        m_hom = re.match(r"\(([IV]+)\)", s[i:])
        if m_hom:
            i += len(m_hom.group(0))
            continue

        j = i + 1
        if j >= len(s):
            i += 1
            continue
        if not LETTER_RE.match(s[j]):
            i += 1
            continue
        j += 1

        # Local substitution pair "(X&Y" is a single reconstruction event.
        if j < len(s) and s[j] == "&":
            j += 1
            if j < len(s) and LETTER_RE.match(s[j]):
                j += 1
            i = j
            continue

        # If another letter follows immediately, it should be marked with "(" too.
        if j < len(s) and LETTER_RE.match(s[j]):
            # Allow weak-initial y-root cluster when only initial y
            # is reconstructed in prefix forms (e.g., "(ytn", "(yṯb").
            if allow_weak_y_cluster and s[i:j] == "(y" and j < len(s) and LETTER_RE.match(s[j]):
                i = j + 1
                continue
            return True
        i = j
    return False


def reconstruct_surface_from_analysis(analysis: str) -> str:
    """
    Reconstruct expected surface letters from one analysis variant.

    Conventions:
    - '(' marks a lexeme letter absent in surface -> omitted from reconstruction.
    - '&X' marks surface-only letter X -> included in reconstruction.
    - substitution '(X&Y' contributes Y to reconstruction.
    - ':d', ':l', ':pass', ... are stem labels, not surface letters.
    - wrappers/markers (!, ], [, /, =, +, ~) are ignored as delimiters.
    - homonym tags '(I)/(II)/...' are ignored.
    """
    a = (analysis or "").strip()
    if not a:
        return ""

    out: List[str] = []
    i = 0
    n = len(a)
    while i < n:
        m_hom = re.match(r"\(([IV]+)\)", a[i:])
        if m_hom:
            i += len(m_hom.group(0))
            continue

        ch = a[i]

        if ch == ":":
            i += 1
            while i < n and re.match(r"[A-Za-z]", a[i]):
                i += 1
            continue

        if ch == "(":
            if i + 1 < n and ANALYSIS_SURFACE_LETTER_RE.match(a[i + 1]):
                if i + 3 < n and a[i + 2] == "&" and ANALYSIS_SURFACE_LETTER_RE.match(a[i + 3]):
                    out.append(a[i + 3])
                    i += 4
                    continue
                # Reconstructed lexeme-only letter, absent in surface.
                i += 2
                continue
            i += 1
            continue

        if ch == "&":
            if i + 1 < n and ANALYSIS_SURFACE_LETTER_RE.match(a[i + 1]):
                out.append(a[i + 1])
                i += 2
                continue
            i += 1
            continue

        if ch in {"!", "]", "[", "/", "=", "+", "~", ",", ")"}:
            i += 1
            continue

        if ANALYSIS_SURFACE_LETTER_RE.match(ch):
            out.append(ch)
        i += 1

    return "".join(out)


def detect_suffix_segment(surface: str) -> Optional[str]:
    """Return recognized clitic suffix segment from surface, if present."""
    s = normalize_surface((surface or "").strip())
    for seg in _CLITIC_SUFFIX_SEGMENTS:
        if len(s) > len(seg) and s.endswith(seg):
            return seg
    return None


def verb_root_lookup_keys(lexeme: str) -> List[str]:
    """Return normalized root spellings used for verb lemma-map lookups."""
    letters = (lexeme or "").strip()
    if not letters:
        return []
    root = "-".join(list(letters))
    keys = [f"/{root}/", f"{root}/", f"/{root}", root]
    out: List[str] = []
    seen = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def choose_lookup_candidates(
    lexeme: str,
    lexeme_candidates: List["DulatEntry"],
    surface_candidates: List["DulatEntry"],
) -> Tuple[List["DulatEntry"], str]:
    """Pick candidate source and lookup mode, with lexeme->surface fallback."""
    if lexeme:
        if lexeme_candidates:
            return lexeme_candidates, "lexeme"
        if surface_candidates:
            return surface_candidates, "surface-fallback"
        return [], "lexeme"
    return surface_candidates, "surface"


def analysis_has_missing_suffix_plus(analysis: str, surface: str) -> bool:
    """True if analysis/surface pair strongly indicates missing '+' suffix split."""
    if "+" in (analysis or ""):
        return False
    seg = detect_suffix_segment(surface)
    if not seg:
        return False

    s_norm = normalize_surface(surface)
    base = s_norm[: -len(seg)]
    variants = split_semicolon_field(analysis) or [analysis]
    for var in variants:
        v = (var or "").strip()
        if not v:
            continue
        core = v.rstrip("/")
        if core.endswith(seg):
            return True
        recon = normalize_surface(reconstruct_surface_from_analysis(v))
        if recon == base:
            return True
    return False


def analysis_has_missing_plural_split(analysis: str, surface: str) -> bool:
    """True if analysis/surface pair strongly indicates missing /m or /t= split."""
    s_norm = normalize_surface(surface)
    if not s_norm.endswith(("m", "t")):
        return False
    target = s_norm[:-1]

    variants = split_semicolon_field(analysis) or [analysis]
    for var in variants:
        v = (var or "").strip()
        if not v:
            continue
        if "/" not in v:
            continue
        if v.endswith(("/m", "/t", "/m=", "/t=")):
            continue
        recon = normalize_surface(reconstruct_surface_from_analysis(v))
        if recon == target:
            return True
    return False


def analysis_has_missing_feminine_singular_split(analysis: str, surface: str) -> bool:
    """True if analysis/surface pair strongly indicates missing feminine '/t' split."""
    s_norm = normalize_surface(surface)
    if not s_norm.endswith("t"):
        return False

    variants = split_semicolon_field(analysis) or [analysis]
    for var in variants:
        v = (var or "").strip()
        if not v or "[" in v:
            continue
        if "/" not in v:
            continue
        if v.endswith(("/t", "/t=")):
            continue
        if not re.match(r"^.+t(?:\([IVX]+\))?/$", v):
            continue
        recon = normalize_surface(reconstruct_surface_from_analysis(v))
        if recon == s_norm:
            return True
    return False


def analysis_has_lexeme_t_split_without_reconstructed_t(analysis: str) -> bool:
    """True when a '/t' split variant lacks lexical '(t' reconstruction."""
    variants = split_semicolon_field(analysis) or [analysis]
    for var in variants:
        v = (var or "").strip()
        if not v or "[" in v:
            continue
        if re.search(r"/t=(?=\s*$|[+;,])", v):
            continue
        if re.search(r"/t(?=\s*$|[+;,])", v) is None:
            continue
        base = re.split(r"/t(?=\s*$|[+;,])", v, maxsplit=1)[0]
        if "(t" not in base:
            return True
    return False


def analysis_has_invalid_enclitic_plus(analysis: str) -> bool:
    """True when analysis uses invalid '~+x' enclitic encoding."""
    variants = split_semicolon_field(analysis) or [analysis]
    return any("~+" in (v or "") for v in variants)


def analysis_has_homonym_marked_n_clitic(analysis: str) -> bool:
    """True when enclitic n is encoded with homonym numerals (invalid in col3)."""
    variants = split_semicolon_field(analysis) or [analysis]
    return any(_HOMONYM_MARKED_N_CLITIC_RE.search((v or "").strip()) for v in variants)


def variant_has_lexeme_terminal_single_suffix_split(
    analysis_variant: str, declared_token: str
) -> bool:
    """Detect '/+n' or '/+y' split when n/y belongs to declared lemma.

    Intended to catch false splits like:
    - mṯ/+n  with DULAT token mṯn
    - lš/+n  with DULAT token lšn
    """
    a_txt = (analysis_variant or "").strip()
    if not a_txt:
        return False
    m_suffix = re.search(r"/\+([ny])(?![A-Za-z])", a_txt)
    if not m_suffix:
        return False
    suffix = m_suffix.group(1)

    d_tok = (declared_token or "").strip()
    if not d_tok:
        return False
    if _DECLARED_SUFFIX_NY_RE.search(d_tok):
        return False

    lemma_raw, _hom = parse_declared_dulat_token(d_tok)
    if not lemma_raw or lemma_raw.startswith("/"):
        return False
    lemma_letters = _DECLARED_LEMMA_LETTER_RE.sub("", normalize_surface(lemma_raw)).lower()
    return bool(lemma_letters) and lemma_letters.endswith(suffix)


def variant_has_baad_plus_n(analysis_variant: str, declared_token: str) -> bool:
    """Detect bʕd forms where enclitic n is encoded with '+' instead of '~'."""
    a_txt = (analysis_variant or "").strip()
    if not a_txt or "+n" not in a_txt:
        return False
    d_tok = (declared_token or "").strip()
    lemma_raw, _hom = parse_declared_dulat_token(d_tok)
    lemma_letters = _DECLARED_LEMMA_LETTER_RE.sub("", normalize_surface(lemma_raw)).lower()
    return lemma_letters == normalize_surface("bʕd")


def _pos_looks_nominal(pos_text: str) -> bool:
    p = (pos_text or "").strip()
    if not p:
        return False
    return any(tag in p for tag in ("n.", "adj.", "num.", "DN", "PN", "TN"))


def row_has_ambiguous_l_in_offering_sequence(
    surface: str,
    analysis_field: str,
    pos_field: str,
    prev_surface: str,
    prev_pos: str,
    next_pos: str,
) -> bool:
    """Detect offering-list context where ambiguous `l` should be preposition."""
    if (surface or "").strip() != "l":
        return False
    if (analysis_field or "").strip() != "l(I);l(II);l(III)":
        return False
    if (pos_field or "").strip() != "prep.;adv.;functor":
        return False

    prev_surface_norm = normalize_surface((prev_surface or "").strip())
    if prev_surface_norm not in _OFFERING_SURFACES:
        return False
    if not _pos_looks_nominal(prev_pos):
        return False

    next_pos_text = (next_pos or "").strip()
    if "vb" in next_pos_text:
        return False
    return _pos_looks_nominal(next_pos_text)


def row_has_baal_labourer_in_ktu1(
    file_path: str,
    surface: str,
    analysis_field: str,
    dulat_field: str,
    pos_field: str,
    gloss_field: str,
) -> bool:
    """Detect forbidden bʕl(I) 'labourer' variant in KTU 1.* rows."""
    if not Path(file_path).name.startswith("KTU 1."):
        return False
    if (surface or "").strip() != "bˤl":
        return False
    if "bˤl(I)/" not in (analysis_field or ""):
        return False
    if "bʕl (I)" not in (dulat_field or ""):
        return False
    if "n. m." not in (pos_field or ""):
        return False
    return "labourer" in (gloss_field or "").lower()


def row_has_mixed_baal_dn_labourer_reading(
    surface: str,
    analysis_field: str,
    dulat_field: str,
    pos_field: str,
    gloss_field: str,
) -> bool:
    """Detect known bad bˤlm ambiguity: Baʿlu(DN) + labourer plural mix."""
    if normalize_surface((surface or "").strip()) != normalize_surface("bʕlm"):
        return False

    analysis_variants = split_semicolon_field(analysis_field)
    dulat_variants = split_semicolon_field(dulat_field)
    pos_variants = split_semicolon_field(pos_field)
    gloss_variants = split_semicolon_field(gloss_field)

    has_ii_variant = any(v in {"bˤl(II)/", "bˤlm(II)/"} for v in analysis_variants)
    has_i_plural_variant = "bˤl(I)/m" in analysis_variants
    if not (has_ii_variant and has_i_plural_variant):
        return False

    has_dulat_ii = "bʕl (II)" in dulat_variants
    has_dulat_i = "bʕl (I)" in dulat_variants
    if not (has_dulat_ii and has_dulat_i):
        return False

    has_dn = any("DN" in p for p in pos_variants)
    has_baalu = any("baʿlu" in (g or "").lower() for g in gloss_variants)
    has_labourer = any("labourer" in (g or "").lower() for g in gloss_variants)
    return has_dn and has_baalu and has_labourer


def dedupe_entries(entries: List["DulatEntry"]) -> List["DulatEntry"]:
    seen = set()
    out = []
    for e in entries:
        if e.entry_id in seen:
            continue
        seen.add(e.entry_id)
        out.append(e)
    return out


STEM_RE = re.compile(r"\b(Gt|Dt|Lt|Nt|Št|Gpass|Dpass|Špass|G|D|L|N|Š)\b")


def extract_stems(morph: str) -> set:
    stems = set()
    for m in STEM_RE.findall(morph or ""):
        stems.add(m)
    return stems


@dataclass
class DulatEntry:
    entry_id: int
    lemma: str
    homonym: str
    pos: str
    gloss: str
    morph: str
    form_text: str


@dataclass
class Issue:
    level: str  # error|warning|info
    file: str
    line_no: int
    line_id: str
    surface: str
    analysis: str
    message: str


# -----------------------------
# DULAT / UDB loaders
# -----------------------------


def load_dulat(dulat_db: Path):
    conn = sqlite3.connect(str(dulat_db))
    cur = conn.cursor()

    cur.execute("SELECT entry_id, text FROM translations ORDER BY entry_id, rowid")
    translations: Dict[int, str] = {}
    for entry_id, text_val in cur.fetchall():
        if entry_id not in translations and text_val:
            translations[entry_id] = text_val

    cur.execute("SELECT entry_id, lemma, homonym, pos, data FROM entries")
    entry_meta: Dict[int, Tuple[str, str, str, str]] = {}
    entry_stems: Dict[int, set] = {}
    entry_gender: Dict[int, str] = {}
    for entry_id, lemma, homonym, pos, data_json in cur.fetchall():
        lemma = (lemma or "").strip()
        homonym = (homonym or "").strip()
        if lemma and not homonym:
            m = re.match(r"^(.*)\s*\(([IV]+)\)\s*$", lemma)
            if m:
                lemma = m.group(1).strip()
                homonym = m.group(2)
        entry_meta[entry_id] = (
            lemma,
            homonym,
            pos or "",
            translations.get(entry_id, ""),
        )

        # Prefer explicit stem metadata from entry JSON when available.
        if data_json:
            try:
                data_obj = json.loads(data_json)
                gender = (data_obj.get("gender") or "").strip()
                if gender:
                    entry_gender[entry_id] = gender
                for stem_item in data_obj.get("stems_structured") or []:
                    stem_name = stem_item.get("name", "")
                    if stem_name:
                        entry_stems.setdefault(entry_id, set()).update(extract_stems(stem_name))
                for form_item in data_obj.get("forms_structured") or []:
                    morph = form_item.get("morphology", "")
                    if morph:
                        entry_stems.setdefault(entry_id, set()).update(extract_stems(morph))
            except Exception:
                pass

    cur.execute("SELECT forms.text, forms.morphology, forms.entry_id FROM forms")
    forms_map: Dict[str, List[DulatEntry]] = {}
    for form_text, morph, entry_id in cur.fetchall():
        if entry_id not in entry_meta or not form_text:
            continue
        lemma, hom, pos, gloss = entry_meta[entry_id]
        if morph:
            entry_stems.setdefault(entry_id, set()).update(extract_stems(morph))
        key = normalize_surface(form_text)
        entry = DulatEntry(
            entry_id=entry_id,
            lemma=lemma,
            homonym=hom,
            pos=pos,
            gloss=gloss,
            morph=morph or "",
            form_text=form_text,
        )
        forms_map.setdefault(key, []).append(entry)

    # Optional disambiguated lemma transliterations (if present in DB)
    lemma_translit: Dict[int, set] = {}
    try:
        cur.execute("SELECT entry_id, translit FROM lemmas")
        for entry_id, translit in cur.fetchall():
            if not translit:
                continue
            t = translit.strip()
            if not t:
                continue
            lemma_translit.setdefault(entry_id, set()).add(t)
    except sqlite3.Error:
        pass

    # Build lemma map for lexeme-based lookups
    lemma_map: Dict[str, List[DulatEntry]] = {}
    for entry_id, (lemma, hom, pos, gloss) in entry_meta.items():
        if not lemma:
            continue
        aliases = set(lemma_aliases(lemma))
        for t in lemma_translit.get(entry_id, set()):
            aliases.add(t)
            # For root-like transliterations, also index slash-wrapped alias.
            if "-" in t and not (t.startswith("/") and t.endswith("/")):
                aliases.add("/" + t + "/")
        for alias in aliases:
            key = normalize_surface(alias)
            lemma_map.setdefault(key, []).append(
                DulatEntry(
                    entry_id=entry_id,
                    lemma=lemma,
                    homonym=hom,
                    pos=pos,
                    gloss=gloss,
                    morph="",
                    form_text="",
                )
            )

    conn.close()
    return forms_map, entry_meta, lemma_map, entry_stems, entry_gender


def load_udb_words(udb_db: Path):
    conn = sqlite3.connect(str(udb_db))
    cur = conn.cursor()
    cur.execute("SELECT word FROM concordance")
    words = {row[0] for row in cur.fetchall() if row and row[0]}
    conn.close()
    return words


# -----------------------------
# Parsing helpers
# -----------------------------

HEAD_RE = re.compile(r"DULAT:\s*([^#;]+?)(?:\s+—|$)")


def parse_dulat_comment(line: str) -> Tuple[Optional[str], Optional[str]]:
    m = HEAD_RE.search(line)
    if not m:
        return None, None
    head = m.group(1).strip()
    # Allow comment heads formatted as "lemma (I) [POS]" by trimming POS.
    head = re.sub(r"\s*\[[^\]]*\]\s*$", "", head).strip()
    if head == "NOT FOUND":
        return None, None
    m_hom = re.match(r"^(.*)\s+\(([IV]+)\)\s*$", head)
    if m_hom:
        return m_hom.group(1).strip(), m_hom.group(2)
    return head, ""


def extract_lexeme_from_analysis(analysis: str) -> Tuple[str, bool, str]:
    """
    Derive lexeme string from analysis.
    Returns (lexeme, is_verb, homonym).
    """
    if not analysis:
        return "", False, ""

    is_verb = "[" in analysis
    hom = ""
    m_hom = re.search(r"\(([IV]+)\)", analysis)
    if m_hom:
        hom = m_hom.group(1)

    # take portion before verb/nominal endings
    if "[" in analysis:
        base = analysis.split("[", 1)[0]
    else:
        base = analysis.split("/", 1)[0]

    # remove homonym markers like (II)
    base = re.sub(r"\([IV]+\)", "", base)

    # strip prefix markers !...! and stem markers ]...]
    while "!" in base:
        m = re.search(r"!.*?!", base)
        if not m:
            break
        base = base[: m.start()] + base[m.end() :]
    while "]" in base:
        m = re.search(r"\].*?\]", base)
        if not m:
            break
        base = base[: m.start()] + base[m.end() :]

    # remove stray markers
    base = base.replace("=", "").replace(":", "").replace("~", "")

    # reconstruct lexeme using ( and &
    res: List[str] = []
    i = 0
    while i < len(base):
        ch = base[i]
        if ch == "(":
            i += 1
            if i < len(base):
                res.append(base[i])
                # if next is &, skip it and the following char
                if i + 1 < len(base) and base[i + 1] == "&":
                    i += 2
                    if i < len(base):
                        i += 1
                else:
                    i += 1
            continue
        if ch == "&":
            # skip this and the next character
            i += 2
            continue
        # skip marker characters
        if ch in {"!", "]", "[", "/", "+"}:
            i += 1
            continue
        res.append(ch)
        i += 1

    lex = "".join(res)
    # Verbal roots: initial a/i/u represent ʔ
    if is_verb and lex and lex[0] in {"a", "i", "u"}:
        lex = "ʔ" + lex[1:]
    return lex, is_verb, hom


ALT_FORM_RE = re.compile(r"\b[!\](/[&\(\)A-Za-z0-9ˤʔḫḫṣṯẓġḏḫḥṭš]+\b")


def extract_alt_forms(comment: str) -> List[str]:
    # Alt forms are introduced by "# OR:", "# or", or "# variant"
    m = re.search(r"\b(?:OR:|or|variant)\b(.*)", comment)
    if not m:
        return []
    tail = m.group(1)
    # stop at another marker or DULAT or ??? etc.
    stop = re.search(r"(#|DULAT:|\\?\\?\\?)", tail)
    if stop:
        tail = tail[: stop.start()]
    tokens = []
    for tok in re.split(r"[;,\\s]+", tail.strip()):
        if tok and any(ch in tok for ch in ("/", "[", "!", "]", "(", "&")):
            tokens.append(tok)
    return tokens


def split_semicolon_field(value: str) -> List[str]:
    if value is None:
        return []
    out = [x.strip() for x in value.split(";")]
    return [x for x in out if x != ""]


def split_csv_field(value: str) -> List[str]:
    if value is None:
        return []
    out = [x.strip() for x in value.split(",")]
    return [x for x in out if x != ""]


def is_unresolved_placeholder(value: str) -> bool:
    tok = (value or "").strip()
    return bool(tok) and re.fullmatch(r"\?+", tok) is not None


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


def normalize_pos_label(value: str) -> str:
    tok = re.sub(r"\s+", " ", (value or "").strip())
    if not tok:
        return ""
    return POS_LABEL_NORMALIZATION.get(tok.lower(), tok)


def is_known_slash_pos_label(value: str) -> bool:
    tok = re.sub(r"\s+", " ", (value or "").strip()).lower()
    return tok in POS_LABEL_NORMALIZATION


def split_pos_options(value: str) -> List[str]:
    """
    Split POS options for a single morpheme token.
    Convention:
      - ',' separates morphemes
      - '/' separates POS options within one morpheme token
    DULAT labels that internally use '/' (e.g., 'det. / rel. functor') are
    normalized to '... or ...' and treated as a single option.
    """
    if value is None:
        return []
    tok = value.strip()
    if not tok:
        return []
    if is_known_slash_pos_label(tok):
        return [normalize_pos_label(tok)]
    parts = [p.strip() for p in re.split(r"(?<!\s)/(?!\s)", tok)]
    return [normalize_pos_label(p) for p in parts if p]


NOUN_GENDER_POS_RE = re.compile(r"n\.\s*(m|f)\.?(?=\s|$|[,;/])", re.IGNORECASE)
NOUN_BASE_POS_RE = re.compile(r"\bn\.\s*", re.IGNORECASE)
ADJ_GENDER_POS_RE = re.compile(r"adj\.\s*(m|f)\.?(?=\s|$|[,;/])", re.IGNORECASE)


def normalize_pos_option_for_validation(value: str) -> str:
    """
    Normalize POS option for comparison against DULAT-allowed labels.
    Allows project-side noun gender enrichment (n. m./n. f.) to match
    DULAT noun labels encoded as plain n.
    """
    tok = normalize_pos_label((value or "").strip())
    tok = strip_plurale_tantum_marker(tok)
    tok = NOUN_GENDER_POS_RE.sub("n ", tok)
    tok = NOUN_BASE_POS_RE.sub("n ", tok)
    tok = ADJ_GENDER_POS_RE.sub("adj.", tok)
    tok = re.sub(r"\s+([,;])", r"\1", tok)
    tok = re.sub(r"\s+", " ", tok).strip()
    return tok.lower()


def extract_noun_gender_from_pos(value: str) -> Optional[str]:
    m = NOUN_GENDER_POS_RE.search(value or "")
    if not m:
        return None
    g = (m.group(1) or "").lower().rstrip(".")
    if g in {"m", "f"}:
        return f"{g}."
    return None


def extract_adj_gender_from_pos(value: str) -> Optional[str]:
    m = ADJ_GENDER_POS_RE.search(value or "")
    if not m:
        return None
    g = (m.group(1) or "").lower().rstrip(".")
    if g in {"m", "f"}:
        return f"{g}."
    return None


def is_cuc_separator_line(raw: str) -> bool:
    return raw.lstrip().startswith("#")


def is_out_tsv_header_row(parts: List[str]) -> bool:
    if len(parts) != 7:
        return False
    lowered = [part.strip().lower() for part in parts]
    return lowered == OUT_TSV_HEADER_COLUMNS


def is_cuc_placeholder_row(parts: List[str]) -> bool:
    """
    Raw cuc_tablets_tsv token rows are typically:
      id<TAB>surface<TAB>surface
    i.e. analysis not yet annotated.
    """
    if len(parts) != 3:
        return False
    line_id = (parts[0] or "").strip()
    surface = (parts[1] or "").strip()
    analysis = (parts[2] or "").strip()
    if not line_id.isdigit():
        return False
    return analysis == surface


def parse_declared_dulat_token(token: str) -> Tuple[str, str]:
    """
    Parse a structured col4 token such as:
      - /q-t-l/
      - bʕl (II)
      - bʕl(II)
    Returns (lemma, homonym).
    """
    tok = (token or "").strip()
    if not tok:
        return "", ""
    m = re.match(r"^(.*?)(?:\s*\(([IV]+)\))?$", tok)
    if not m:
        return tok, ""
    lemma = (m.group(1) or "").strip()
    hom = (m.group(2) or "").strip()
    return lemma, hom


def declared_lemma_looks_t_final(lemma: str) -> bool:
    """Conservative check whether a declared DULAT lemma is t-final."""
    normalized = normalize_surface((lemma or "").strip())
    if not normalized:
        return False
    raw_letters = _DECLARED_LEMMA_LETTER_RE.sub("", normalized).lower()
    normalized_no_tail_group = re.sub(r"\([^)]*\)\s*$", "", normalized).strip()
    trimmed_letters = _DECLARED_LEMMA_LETTER_RE.sub("", normalized_no_tail_group).lower()
    return raw_letters.endswith("t") or trimmed_letters.endswith("t")


def extract_homonyms_for_lemma(analysis_field: str, dulat_field: str, lemma: str) -> set:
    """
    Collect homonym markers for a lemma from row-level analysis (col3)
    and declared DULAT entries (col4).
    """
    out = set()
    lemma_norm = normalize_surface(lemma)

    analysis_variants = split_semicolon_field(analysis_field) or (
        [analysis_field.strip()] if analysis_field else []
    )
    for a_var in analysis_variants:
        a_txt = (a_var or "").strip()
        m = re.match(rf"^{re.escape(lemma)}\(([IV]+)\)", a_txt)
        if m:
            out.add(m.group(1))

    for d_var in split_semicolon_field(dulat_field):
        for dtok in split_csv_field(d_var):
            d_lemma, d_hom = parse_declared_dulat_token(dtok)
            if d_hom and normalize_surface(d_lemma) == lemma_norm:
                out.add(d_hom)
    return out


def variant_is_weak_initial_y_verb(analysis_variant: str, d_field: str) -> bool:
    a_txt = (analysis_variant or "").strip()
    if "[" not in a_txt:
        return False
    d_tokens = split_csv_field(d_field)
    if not d_tokens:
        return False
    lemma_tok, _hom_tok = parse_declared_dulat_token(d_tokens[0])
    lemma_norm = normalize_surface(lemma_tok)
    return lemma_norm.startswith("/y-")


def variant_is_weak_initial_y_prefix_form(analysis_variant: str, d_field: str) -> bool:
    a_txt = (analysis_variant or "").strip()
    if not variant_is_weak_initial_y_verb(a_txt, d_field):
        return False
    return bool(re.search(r"![ytan]!", a_txt))


def variant_root_radicals(d_field: str) -> Optional[Tuple[str, str, str]]:
    d_tokens = split_csv_field(d_field)
    if not d_tokens:
        return None
    lemma_tok, _hom_tok = parse_declared_dulat_token(d_tokens[0])
    lemma_tok = (lemma_tok or "").strip()
    if not (lemma_tok.startswith("/") and lemma_tok.endswith("/")):
        return None
    core = lemma_tok[1:-1]
    radicals = [seg.strip() for seg in core.split("-") if seg.strip()]
    if len(radicals) != 3:
        return None
    return radicals[0], radicals[1], radicals[2]


def entry_pos_options(pos_raw: str) -> List[str]:
    """
    Convert DULAT POS cell into acceptable single-tag values.
    Example: 'n., DN' -> ['n.', 'DN']
    """
    if not pos_raw:
        return []
    return [normalize_pos_label(p.strip()) for p in pos_raw.split(",") if p.strip()]


def pos_token_is_ambiguous(pos_tok: str) -> bool:
    t = (pos_tok or "").strip().lower()
    if not t:
        return False
    if len(split_pos_options(t)) > 1:
        return True
    return ("|" in t) or (";" in t)


# -----------------------------
# Linter
# -----------------------------


def lint_file(
    path: Path,
    dulat_forms: Dict[str, List[DulatEntry]],
    entry_meta,
    lemma_map: Dict[str, List[DulatEntry]],
    entry_stems: Dict[int, set],
    entry_gender: Dict[int, str],
    udb_words,
    baseline: Optional[Path],
    input_format: str = "auto",
    db_checks: bool = True,
):
    issues: List[Issue] = []

    lines = path.read_text(encoding="utf-8").splitlines()
    is_out_tsv_file = path.parent.name == "out"

    # Baseline map for CUC comparison
    baseline_map = {}
    if baseline and baseline.exists():
        for line in baseline.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                baseline_map[parts[0]] = parts[1]

    if is_out_tsv_file:
        first_non_empty_line = None
        for line_no, raw in enumerate(lines, 1):
            if raw.strip():
                first_non_empty_line = (line_no, raw)
                break
        if first_non_empty_line is None or not is_out_tsv_header_row(
            first_non_empty_line[1].split("\t")
        ):
            line_no = first_non_empty_line[0] if first_non_empty_line else 1
            issues.append(
                Issue(
                    "error",
                    str(path),
                    line_no,
                    "",
                    "",
                    "",
                    "Missing or invalid TSV header row in out/*.tsv",
                )
            )

    data_parts_by_line: Dict[int, List[str]] = {}
    data_line_numbers: List[int] = []
    for line_no, raw in enumerate(lines, 1):
        if not raw.strip() or is_cuc_separator_line(raw):
            continue
        core = raw
        if (not is_out_tsv_file) and "#" in raw:
            core, _comment = raw.split("#", 1)
            core = core.rstrip()
        parts = core.split("\t")
        if is_out_tsv_file and is_out_tsv_header_row(parts):
            continue
        if len(parts) >= 3:
            data_parts_by_line[line_no] = parts
            data_line_numbers.append(line_no)

    prev_data_line: Dict[int, Optional[int]] = {}
    next_data_line: Dict[int, Optional[int]] = {}
    for idx, line_no in enumerate(data_line_numbers):
        prev_data_line[line_no] = data_line_numbers[idx - 1] if idx > 0 else None
        next_data_line[line_no] = (
            data_line_numbers[idx + 1] if idx + 1 < len(data_line_numbers) else None
        )

    prev_id = None

    # For parsing consistency (by surface form)
    surface_to_analyses: Dict[str, set] = {}
    surface_to_ids: Dict[str, set] = {}
    lemma_to_stems: Dict[str, set] = {}
    lemma_stem_ids: Dict[Tuple[str, str], set] = {}
    lemma_stem_lines: Dict[Tuple[str, str], set] = {}
    seen_pairs: List[Tuple[str, Tuple[str, str]]] = []
    token_rows: List[Dict[str, str]] = []
    entry_index: Dict[Tuple[str, str], set] = {}
    entry_gender_index: Dict[Tuple[str, str], set] = {}
    for _entry_id, (lemma, hom, pos, _gloss) in entry_meta.items():
        if not lemma:
            continue
        key = (normalize_surface(lemma), hom or "")
        entry_index.setdefault(key, set()).add(pos or "")
    for _entry_id, (lemma, hom, _pos, _gloss) in entry_meta.items():
        if not lemma:
            continue
        g = (entry_gender.get(_entry_id) or "").strip().lower()
        if g not in {"m.", "f."}:
            continue
        key = (normalize_surface(lemma), hom or "")
        entry_gender_index.setdefault(key, set()).add(g)

    for i, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        if is_cuc_separator_line(raw):
            continue
        comment = ""
        core = raw
        if (not is_out_tsv_file) and "#" in raw:
            core, comment = raw.split("#", 1)
            core = core.rstrip()
            comment = comment.strip()
        parts = core.split("\t")
        if is_out_tsv_file and is_out_tsv_header_row(parts):
            continue

        if is_out_tsv_file and len(parts) != 7:
            issues.append(
                Issue(
                    "error",
                    str(path),
                    i,
                    parts[0] if parts else "",
                    parts[1] if len(parts) > 1 else "",
                    parts[2] if len(parts) > 2 else "",
                    f"Expected exactly 7 columns in out/*.tsv row, got {len(parts)}",
                )
            )

        if len(parts) < 3:
            issues.append(
                Issue(
                    "error",
                    str(path),
                    i,
                    parts[0] if parts else "",
                    "",
                    "",
                    "Missing tabs / columns",
                )
            )
            continue

        line_id, surface, analysis = parts[0], parts[1], parts[2]
        in_cuc_dir = "cuc_tablets_tsv" in str(path)
        is_raw_cuc_row = False
        if input_format == "cuc_tablets_tsv":
            is_raw_cuc_row = is_cuc_placeholder_row(parts)
        elif input_format == "auto":
            is_raw_cuc_row = is_cuc_placeholder_row(parts) and (
                in_cuc_dir or path.suffix.lower() == ".tsv"
            )

        analysis_variants = [analysis.strip()] if analysis.strip() else [analysis]
        declared_head: Optional[str] = None
        declared_hom: Optional[str] = None
        dulat_variants: List[str] = []
        pos_variants: List[str] = []
        gloss_variants: List[str] = []
        # For clitic ambiguity resolution: map declared col4 token -> selected col5 POS
        selected_pos_by_declared: Dict[Tuple[str, str], str] = {}
        unresolved_declared_variant_indexes = set()

        # Structured 6-column format:
        # 1=id, 2=surface, 3=analysis variants, 4=DULAT entries, 5=POS tags, 6=glosses
        if len(parts) >= 6:
            analysis_variants = split_semicolon_field(parts[2]) or (
                [parts[2].strip()] if parts[2].strip() else []
            )
            dulat_variants = split_semicolon_field(parts[3])
            pos_variants = split_semicolon_field(parts[4])
            gloss_variants = split_semicolon_field(parts[5])

            has_core_letters = has_letters(strip_missing(surface).strip()) or any(
                has_letters(strip_missing(v)) for v in analysis_variants if v
            )

            prev_parts = data_parts_by_line.get(prev_data_line.get(i) or -1)
            next_parts = data_parts_by_line.get(next_data_line.get(i) or -1)
            prev_surface = prev_parts[1] if prev_parts and len(prev_parts) > 1 else ""
            prev_pos_field = prev_parts[4] if prev_parts and len(prev_parts) > 4 else ""
            next_pos_field = next_parts[4] if next_parts and len(next_parts) > 4 else ""

            if row_has_ambiguous_l_in_offering_sequence(
                surface=surface,
                analysis_field=parts[2],
                pos_field=parts[4],
                prev_surface=prev_surface,
                prev_pos=prev_pos_field,
                next_pos=next_pos_field,
            ):
                issues.append(
                    Issue(
                        "warning",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "In offering-list sequences, parse 'l' as l(I) preposition",
                    )
                )

            if row_has_baal_labourer_in_ktu1(
                file_path=str(path),
                surface=surface,
                analysis_field=parts[2],
                dulat_field=parts[3],
                pos_field=parts[4],
                gloss_field=parts[5],
            ):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "In KTU 1.*, remove bʕl(I) 'labourer' and keep bʕl (II) /b-ʕ-l/ readings",
                    )
                )

            if row_has_mixed_baal_dn_labourer_reading(
                surface=surface,
                analysis_field=parts[2],
                dulat_field=parts[3],
                pos_field=parts[4],
                gloss_field=parts[5],
            ):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "bˤlm must not mix Baʿlu(DN) with labourer plural; use noun plural bˤl(II)/m",
                    )
                )

            if analysis_variants:
                analysis = analysis_variants[0]

            if (
                analysis_variants
                and dulat_variants
                and len(dulat_variants) != len(analysis_variants)
            ):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Column 4 count must match analysis variant count",
                    )
                )
            if analysis_variants and pos_variants and len(pos_variants) != len(analysis_variants):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Column 5 count must match analysis variant count",
                    )
                )
            if (
                analysis_variants
                and gloss_variants
                and len(gloss_variants) != len(analysis_variants)
            ):
                issues.append(
                    Issue(
                        "warning",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Column 6 count should match analysis variant count",
                    )
                )

            # Validate declared DULAT entries and POS tags in structured columns.
            if has_core_letters:
                for vi, a_var in enumerate(analysis_variants):
                    d_field = dulat_variants[vi] if vi < len(dulat_variants) else ""
                    p_field = pos_variants[vi] if vi < len(pos_variants) else ""
                    g_field = gloss_variants[vi] if vi < len(gloss_variants) else ""
                    d_tokens = split_csv_field(d_field)
                    # POS structure:
                    #   ';' variant groups, ',' morphemes, '/' POS options.
                    p_tokens = split_csv_field(p_field)
                    # Gloss fields frequently contain commas as punctuation for a
                    # single lexeme gloss (e.g., "earth, ground"). Only treat
                    # commas as token separators when multiple DULAT tokens are
                    # declared for the variant.
                    if len(d_tokens) <= 1:
                        g_tokens = [g_field.strip()] if g_field.strip() else []
                    else:
                        # Prefer right-splitting so commas inside the main gloss
                        # do not inflate token count for clitic/enclitic tails.
                        g_tokens = [
                            p.strip() for p in g_field.rsplit(",", len(d_tokens) - 1) if p.strip()
                        ]

                    if not d_tokens:
                        issues.append(
                            Issue(
                                "error",
                                str(path),
                                i,
                                line_id,
                                surface,
                                a_var,
                                "Missing DULAT entry token(s) in column 4",
                            )
                        )
                        continue
                    unresolved_analysis = is_unresolved_placeholder(a_var)
                    unresolved_declared = all(is_unresolved_placeholder(x) for x in d_tokens)
                    if unresolved_analysis:
                        if not unresolved_declared:
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    a_var,
                                    "Morphology placeholder '?' should use unresolved DULAT placeholder '?' in column 4",
                                )
                            )
                        if p_tokens and any(not is_unresolved_placeholder(x) for x in p_tokens):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    a_var,
                                    "Unresolved morphology placeholder '?' should use '?' or empty POS",
                                )
                            )
                        if g_tokens and any(not is_unresolved_placeholder(x) for x in g_tokens):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    a_var,
                                    "Unresolved morphology placeholder '?' should use '?' or empty gloss",
                                )
                            )
                        if unresolved_declared:
                            unresolved_declared_variant_indexes.add(vi)
                        continue
                    if unresolved_declared:
                        unresolved_declared_variant_indexes.add(vi)
                        # Explicit unresolved placeholder variant.
                        issues.append(
                            Issue(
                                "warning",
                                str(path),
                                i,
                                line_id,
                                surface,
                                a_var,
                                "Unresolved DULAT placeholder '?' should also use '?' in morphology (column 3)",
                            )
                        )
                        if p_tokens and any(not is_unresolved_placeholder(x) for x in p_tokens):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    a_var,
                                    "Unresolved DULAT placeholder '?' should use '?' or empty POS",
                                )
                            )
                        if g_tokens and any(not is_unresolved_placeholder(x) for x in g_tokens):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    a_var,
                                    "Unresolved DULAT placeholder '?' should use '?' or empty gloss",
                                )
                            )
                        continue
                    if len(p_tokens) > len(d_tokens):
                        issues.append(
                            Issue(
                                "error",
                                str(path),
                                i,
                                line_id,
                                surface,
                                a_var,
                                "POS tokens must map to existing DULAT tokens in column 4",
                            )
                        )
                    if len(g_tokens) > len(d_tokens):
                        issues.append(
                            Issue(
                                "error",
                                str(path),
                                i,
                                line_id,
                                surface,
                                a_var,
                                "Gloss tokens must map to existing DULAT tokens in column 4",
                            )
                        )

                    for di, dtok in enumerate(d_tokens):
                        lemma_tok, hom_tok = parse_declared_dulat_token(dtok)
                        if not lemma_tok:
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    a_var,
                                    "Empty DULAT token in column 4",
                                )
                            )
                            continue

                        if di < len(p_tokens):
                            pos_tok = p_tokens[di].strip()
                            if is_known_slash_pos_label(pos_tok):
                                suggested = normalize_pos_label(pos_tok)
                                issues.append(
                                    Issue(
                                        "warning",
                                        str(path),
                                        i,
                                        line_id,
                                        surface,
                                        a_var,
                                        f"Replace '/' with 'or' in POS label: '{pos_tok}' -> '{suggested}'",
                                    )
                                )

                        if not db_checks:
                            continue

                        key = (normalize_surface(lemma_tok), hom_tok or "")
                        pos_matches = set(entry_index.get(key, set()))
                        gender_matches = set(entry_gender_index.get(key, set()))
                        # Fallback: if homonym omitted in col4 token, allow any homonym with same lemma.
                        if not pos_matches and not hom_tok:
                            for (k_lemma, _k_hom), pos_set in entry_index.items():
                                if k_lemma == normalize_surface(lemma_tok):
                                    pos_matches.update(pos_set)
                        if not gender_matches and not hom_tok:
                            for (k_lemma, _k_hom), g_set in entry_gender_index.items():
                                if k_lemma == normalize_surface(lemma_tok):
                                    gender_matches.update(g_set)
                        if not pos_matches:
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    a_var,
                                    f"Unknown DULAT token in column 4: {dtok}",
                                )
                            )
                            continue

                        if di < len(p_tokens):
                            pos_tok = p_tokens[di].strip()
                            allowed = set()
                            for pos_raw in pos_matches:
                                for opt in entry_pos_options(pos_raw):
                                    allowed.add(normalize_pos_option_for_validation(opt))
                                    for sub_opt in split_pos_options(opt):
                                        allowed.add(normalize_pos_option_for_validation(sub_opt))
                            pos_tok_opts = split_pos_options(pos_tok) if pos_tok else []
                            for opt in pos_tok_opts:
                                opt_norm = normalize_pos_option_for_validation(opt)
                                if opt and allowed and opt_norm not in allowed:
                                    allowed_list = ", ".join(sorted(allowed))
                                    issues.append(
                                        Issue(
                                            "error",
                                            str(path),
                                            i,
                                            line_id,
                                            surface,
                                            a_var,
                                            f"POS token '{opt}' not allowed for {dtok}; choose one of: {allowed_list}",
                                        )
                                    )

                            noun_like_token = any(
                                re.search(r"\bn(?:\.|\b)", (opt or "").lower())
                                for opt in pos_tok_opts
                            )
                            adj_like_token = any(
                                "adj." in (opt or "").lower() for opt in pos_tok_opts
                            )
                            noun_gender = extract_noun_gender_from_pos(pos_tok)
                            adj_gender = extract_adj_gender_from_pos(pos_tok)
                            if noun_like_token and len(gender_matches) == 1:
                                expected_gender = next(iter(gender_matches))
                                if noun_gender is None:
                                    issues.append(
                                        Issue(
                                            "warning",
                                            str(path),
                                            i,
                                            line_id,
                                            surface,
                                            a_var,
                                            f"Noun POS should include DULAT gender marker for {dtok}: n. {expected_gender}",
                                        )
                                    )
                                elif noun_gender != expected_gender:
                                    issues.append(
                                        Issue(
                                            "error",
                                            str(path),
                                            i,
                                            line_id,
                                            surface,
                                            a_var,
                                            f"Noun POS gender mismatch for {dtok}: expected n. {expected_gender}, got n. {noun_gender}",
                                        )
                                    )
                            if adj_like_token and len(gender_matches) == 1:
                                expected_gender = next(iter(gender_matches))
                                if adj_gender is None:
                                    issues.append(
                                        Issue(
                                            "warning",
                                            str(path),
                                            i,
                                            line_id,
                                            surface,
                                            a_var,
                                            f"Adjective POS should include DULAT gender marker for {dtok}: adj. {expected_gender}",
                                        )
                                    )
                                elif adj_gender != expected_gender:
                                    issues.append(
                                        Issue(
                                            "error",
                                            str(path),
                                            i,
                                            line_id,
                                            surface,
                                            a_var,
                                            f"Adjective POS gender mismatch for {dtok}: expected adj. {expected_gender}, got adj. {adj_gender}",
                                        )
                                    )
                            selected_pos_by_declared[
                                (normalize_surface(lemma_tok), hom_tok or "")
                            ] = pos_tok

            if analysis_variants and dulat_variants:
                first_d = split_csv_field(dulat_variants[0])
                if first_d and not all(is_unresolved_placeholder(x) for x in first_d):
                    declared_head, declared_hom = parse_declared_dulat_token(first_d[0])
        seen_pairs.append((line_id, (surface, analysis)))

        # Check numbering order
        try:
            num_id = int(line_id)
            if prev_id is not None and num_id < prev_id:
                issues.append(
                    Issue(
                        "warning",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Line numbers not increasing",
                    )
                )
            prev_id = num_id
        except ValueError:
            issues.append(
                Issue(
                    "warning",
                    str(path),
                    i,
                    line_id,
                    surface,
                    analysis,
                    "Non-numeric line id",
                )
            )

        # Compare with baseline (CUC)
        if baseline_map:
            if line_id not in baseline_map:
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Line id missing in baseline",
                    )
                )
            else:
                base_surface = baseline_map[line_id]
                if normalize_surface(base_surface) != normalize_surface(surface):
                    issues.append(
                        Issue(
                            "error",
                            str(path),
                            i,
                            line_id,
                            surface,
                            analysis,
                            "Surface differs from baseline",
                        )
                    )
                else:
                    # Detect missing ʿ/ʕ → ˤ normalization
                    if any(ch in base_surface for ch in ("ʿ", "ʕ")) and any(
                        ch in surface for ch in ("ʿ", "ʕ")
                    ):
                        issues.append(
                            Issue(
                                "warning",
                                str(path),
                                i,
                                line_id,
                                surface,
                                analysis,
                                "Surface not normalized: ʿ/ʕ should be ˤ",
                            )
                        )

        # Raw cuc_tablets_tsv rows are source tokens, not morphology parses.
        # Keep only structural checks (above) and skip morphology-specific lint.
        if is_raw_cuc_row:
            continue

        token_rows.append(
            {
                "line_no": str(i),
                "line_id": line_id,
                "surface": surface,
                "analysis_field": parts[2] if len(parts) >= 3 else analysis,
                "dulat_field": parts[3] if len(parts) >= 4 else "",
                "pos_field": parts[4] if len(parts) >= 5 else "",
                "gloss_field": parts[5] if len(parts) >= 6 else "",
            }
        )

        # Unicode constraints in columns 2-3
        for bad in ("ʕ", "ʿ", "ả", "ỉ", "ủ"):
            if bad in surface or bad in analysis:
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        f"Disallowed character in columns 2-3: {bad}",
                    )
                )
                break
        # ʔ is allowed only as a reconstructed radical after '(' in column 3; never in column 2
        if "ʔ" in surface:
            issues.append(
                Issue(
                    "error",
                    str(path),
                    i,
                    line_id,
                    surface,
                    analysis,
                    "Disallowed character in column 2: ʔ",
                )
            )
        elif "ʔ" in analysis and "(ʔ" not in analysis:
            issues.append(
                Issue(
                    "error",
                    str(path),
                    i,
                    line_id,
                    surface,
                    analysis,
                    "ʔ must be preceded by '(' in column 3",
                )
            )

        # Check ( precedes & only when they are part of the same substitution sequence
        if "(" in analysis and "&" in analysis:
            if re.search(r"&[^A-Za-zˤʔḫṣṯẓġḏḥṭš]*\(", analysis):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "'&' appears before '('",
                    )
                )
        variant_texts = analysis_variants or ([analysis.strip()] if analysis.strip() else [])
        if not variant_texts:
            variant_texts = [analysis]
        for vi, a_var in enumerate(variant_texts):
            a_txt = (a_var or "").strip()
            if not a_txt:
                continue
            d_field = dulat_variants[vi] if vi < len(dulat_variants) else ""
            if "~+" in a_txt:
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        a_txt,
                        "Enclitic marker '~' must not be followed by '+' (use '~n'/'~y')",
                    )
                )
            if analysis_has_homonym_marked_n_clitic(a_txt):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        a_txt,
                        "Do not use homonym numerals for enclitic n in col3; use +n/+n=/~n/[n/[n=",
                    )
                )
            if variant_has_lexeme_terminal_single_suffix_split(a_txt, d_field):
                issues.append(
                    Issue(
                        "warning",
                        str(path),
                        i,
                        line_id,
                        surface,
                        a_txt,
                        "Lexeme-final n/y should stay in stem; avoid '/+n' or '/+y' split without explicit DULAT suffix token",
                    )
                )
            if variant_has_baad_plus_n(a_txt, d_field):
                issues.append(
                    Issue(
                        "warning",
                        str(path),
                        i,
                        line_id,
                        surface,
                        a_txt,
                        "For bʕd with enclitic n, use '~n' (not '+n')",
                    )
                )
            is_weak_initial_y_verb = variant_is_weak_initial_y_verb(a_txt, d_field)
            if variant_is_weak_initial_y_prefix_form(a_txt, d_field) and "(y" not in a_txt:
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        a_txt,
                        "For weak-initial /y-.../ prefix forms, mark preformative in !...! and reconstruct hidden initial radical as '(y'",
                    )
                )
            root_radicals = variant_root_radicals(d_field)
            has_prefix_preformative = bool(re.search(r"![ytan](?:=|==|===)?!", a_txt))
            if (
                root_radicals
                and root_radicals[2] in {"y", "w"}
                and root_radicals[1] != "t"
                and surface.endswith("t")
                and "[" in a_txt
                and "/" not in a_txt
                and not has_prefix_preformative
                and "[t" not in a_txt
                and not is_unresolved_placeholder(a_txt)
            ):
                issues.append(
                    Issue(
                        "warning",
                        str(path),
                        i,
                        line_id,
                        surface,
                        a_txt,
                        "Weak-final finite verb with surface '-t' should encode suffix-conjugation ending as '[t'",
                    )
                )
            allow_weak_y_cluster = is_weak_initial_y_verb and "(y" in a_txt
            if has_unprefixed_reconstructed_sequence(
                a_txt, allow_weak_y_cluster=allow_weak_y_cluster
            ):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        a_txt,
                        "Each reconstructed letter must be prefixed by '('",
                    )
                )

        # Check ! pairs in analysis
        if analysis.count("!") % 2 != 0:
            issues.append(
                Issue(
                    "error",
                    str(path),
                    i,
                    line_id,
                    surface,
                    analysis,
                    "Unpaired '!' marker",
                )
            )

        note_text = "\t".join(parts[6:]).strip() if len(parts) > 6 else ""
        annotation_text = " ".join(x for x in (note_text, comment) if x).strip()

        # Comments TODO markers
        todo_markers = ("merge", "???", "todo", "fix", "repair")
        annotation_lower = annotation_text.lower()
        hit_markers = [t for t in todo_markers if t in annotation_lower]
        if hit_markers:
            issues.append(
                Issue(
                    "warning",
                    str(path),
                    i,
                    line_id,
                    surface,
                    analysis,
                    f"TODO/uncertain marker in comment: {', '.join(hit_markers)}",
                )
            )

        surface_clean = strip_missing(surface).strip()

        # Column 3 must be sufficient to reconstruct the original surface form.
        if surface_clean and "x" not in surface.lower():
            expected_letters = "".join(
                ch for ch in surface_clean if ANALYSIS_SURFACE_LETTER_RE.match(ch)
            )
            expected_norm = normalize_surface(expected_letters)
            if not expected_norm:
                expected_norm = normalize_surface(surface_clean)
            for a_var in analysis_variants or [analysis]:
                a_txt = (a_var or "").strip()
                if not a_txt:
                    continue
                if is_unresolved_placeholder(a_txt):
                    continue
                reconstructed = normalize_surface(reconstruct_surface_from_analysis(a_txt))
                if reconstructed != expected_norm:
                    issues.append(
                        Issue(
                            "error",
                            str(path),
                            i,
                            line_id,
                            surface,
                            a_txt,
                            f"Analysis does not reconstruct to surface (reconstructs as: {reconstructed})",
                        )
                    )

        # UDB compare
        if udb_words is not None and surface_clean and surface_clean not in {"ˤ", "ʕ", "ʿ"}:
            udb_key = normalize_udb(surface_clean)
            if udb_key not in udb_words:
                issues.append(
                    Issue(
                        "info",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Surface not found in UDB concordance",
                    )
                )

        if db_checks:
            # Handle clitic splits (e.g., b+h=). Base lexeme is checked normally.
            analysis_for_lexeme = analysis
            clitic_parts: List[str] = []
            if "+" in analysis:
                parts = analysis.split("+")
                base_part = parts[0].strip()
                clitic_parts.extend([p for p in parts[1:] if p.strip()])
                analysis_for_lexeme = base_part

            if "[" in analysis:
                base, tail = analysis.split("[", 1)
                analysis_for_lexeme = base.strip()
                tail = tail.strip()
                if tail:
                    for seg in tail.split("+"):
                        seg = seg.strip()
                        if seg:
                            clitic_parts.append(seg)

            seen_clitics = set()
            for part in clitic_parts:
                part = part.lstrip("~")
                if not part:
                    continue
                if part.startswith(":"):
                    continue
                if ":" in part:
                    # Post-[ finite endings can carry stem labels (e.g., t:n).
                    # These are verbal morphology, not clitic lexeme parts.
                    continue
                if not has_letters(strip_markers_simple(part)):
                    continue
                if part in seen_clitics:
                    continue
                seen_clitics.add(part)
                part_lexeme, _, part_hom = extract_lexeme_from_analysis(part)
                if not part_lexeme:
                    continue
                part_candidates: List[DulatEntry] = []
                if part_lexeme:
                    # In +clitic slots, prefer suffix entries (-x) over free lexemes (x)
                    # when both exist; this avoids false ambiguity for parts like +k, +h.
                    suffix_candidates = lemma_map.get(normalize_surface("-" + part_lexeme), [])
                    if suffix_candidates:
                        part_candidates.extend(suffix_candidates)
                    else:
                        part_candidates.extend(lemma_map.get(normalize_surface(part_lexeme), []))
                    if part_hom:
                        part_candidates = [c for c in part_candidates if c.homonym == part_hom]
                if not part_candidates:
                    part_surface = strip_markers_simple(part)
                    if part_surface:
                        part_candidates.extend(dulat_forms.get(normalize_surface(part_surface), []))
                        if part_hom:
                            part_candidates = [c for c in part_candidates if c.homonym == part_hom]
                if not part_candidates:
                    issues.append(
                        Issue(
                            "error",
                            str(path),
                            i,
                            line_id,
                            surface,
                            analysis,
                            f"No DULAT entry found for clitic part: {part}",
                        )
                    )
                else:
                    pos_set = {c.pos for c in part_candidates if c.pos}
                    if len(pos_set) > 1:
                        # DULAT ambiguity for clitics is acceptable if column 5
                        # resolves it. Report only when POS selection itself is
                        # ambiguous.
                        selected_pos_tok = ""
                        norm_part = normalize_surface(part_lexeme)
                        cand_keys = [
                            (norm_part, part_hom or ""),
                            (normalize_surface("-" + part_lexeme), part_hom or ""),
                        ]
                        if part_hom:
                            cand_keys.extend(
                                [
                                    (norm_part, ""),
                                    (normalize_surface("-" + part_lexeme), ""),
                                ]
                            )
                        for ck in cand_keys:
                            if ck in selected_pos_by_declared and selected_pos_by_declared[ck]:
                                selected_pos_tok = selected_pos_by_declared[ck]
                                break
                        if selected_pos_tok and pos_token_is_ambiguous(selected_pos_tok):
                            pos_list = ", ".join(sorted(pos_set))
                            issues.append(
                                Issue(
                                    "info",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    f"POS ambiguous in DULAT for clitic part {part}: {pos_list}; POS column token is ambiguous: {selected_pos_tok}",
                                )
                            )

            # DULAT candidates (prefer lexeme from base analysis)
            analysis_for_lexeme = strip_missing(analysis_for_lexeme).strip()
            is_verb_global = "[" in analysis
            lexeme, is_verb, lex_hom = extract_lexeme_from_analysis(analysis_for_lexeme)
            if is_verb_global:
                is_verb = True
                if lexeme and lexeme[0] in {"a", "i", "u"}:
                    lexeme = "ʔ" + lexeme[1:]
            is_noun = ("/" in analysis_for_lexeme) and (not is_verb_global)
            is_deverbal = is_verb_global and ("/" in analysis)
            has_sh_stem = "]š]" in analysis
            has_t_stem = "]t]" in analysis
            has_colon_stem = re.search(r":[A-Za-z]+", analysis) is not None
            analysis_has_stem = has_sh_stem or has_t_stem or has_colon_stem

            base_candidates: List[DulatEntry] = []
            root_candidates: List[DulatEntry] = []
            verb_candidates_for_stem: List[DulatEntry] = []
            if lexeme:
                lex_key = normalize_surface(lexeme)
                base_candidates.extend(lemma_map.get(lex_key, []))
                if is_verb_global:
                    for root_key in verb_root_lookup_keys(lexeme):
                        root_candidates.extend(lemma_map.get(normalize_surface(root_key), []))
                verb_candidates_for_stem = [
                    c for c in (base_candidates + root_candidates) if "vb" in c.pos.lower()
                ]
                if lex_hom:
                    verb_candidates_for_stem = [
                        c for c in verb_candidates_for_stem if c.homonym == lex_hom
                    ]

            lexeme_candidates: List[DulatEntry] = []
            if is_deverbal and lexeme:
                verb_candidates = [
                    c for c in (base_candidates + root_candidates) if "vb" in c.pos.lower()
                ]
                noun_candidates = [c for c in base_candidates if "vb" not in c.pos.lower()]
                if lex_hom:
                    verb_candidates = [c for c in verb_candidates if c.homonym == lex_hom]
                    noun_candidates = [c for c in noun_candidates if c.homonym == lex_hom]
                if verb_candidates and noun_candidates:
                    issues.append(
                        Issue(
                            "error",
                            str(path),
                            i,
                            line_id,
                            surface,
                            analysis,
                            "Deverbal form matches both verb and noun entries in DULAT",
                        )
                    )
                elif noun_candidates and not verb_candidates:
                    issues.append(
                        Issue(
                            "warning",
                            str(path),
                            i,
                            line_id,
                            surface,
                            analysis,
                            "Deverbal form marked with '[' but only noun entry found in DULAT",
                        )
                    )
                lexeme_candidates = dedupe_entries(verb_candidates + noun_candidates)
            elif base_candidates or root_candidates:
                lexeme_candidates = base_candidates + root_candidates

                # Prefer verb/non-verb candidates based on analysis
                if lexeme_candidates:
                    if is_verb:
                        lexeme_candidates = [c for c in lexeme_candidates if "vb" in c.pos.lower()]
                    elif is_noun:
                        non_vb = [c for c in lexeme_candidates if "vb" not in c.pos.lower()]
                        if non_vb:
                            lexeme_candidates = non_vb
                    else:
                        non_vb = [c for c in lexeme_candidates if "vb" not in c.pos.lower()]
                        if non_vb:
                            lexeme_candidates = non_vb
                    if lex_hom:
                        lexeme_candidates = [c for c in lexeme_candidates if c.homonym == lex_hom]

            analysis_plain = analysis.strip()
            # Surface-only excised tokens (for example "&š") intentionally carry no lexical parse.
            is_surface_only_excised = (
                analysis_plain.startswith("&")
                and "/" not in analysis_plain
                and "[" not in analysis_plain
                and "(" not in analysis_plain
                and "+" not in analysis_plain
                and "~" not in analysis_plain
            )
            skip_dulat = (
                (not lexeme and (not surface_clean or surface_clean in {"ˤ", "ʕ", "ʿ"}))
                or (lexeme in {"ˤ", "ʕ", "ʿ"})
                or is_surface_only_excised
                or is_unresolved_placeholder(analysis_plain)
                or (0 in unresolved_declared_variant_indexes)
            )
            lookup_mode = "surface"
            if skip_dulat:
                d_candidates = []
            else:
                surface_candidates = dulat_forms.get(normalize_surface(surface_clean), [])
                d_candidates, lookup_mode = choose_lookup_candidates(
                    lexeme=lexeme,
                    lexeme_candidates=lexeme_candidates,
                    surface_candidates=surface_candidates,
                )
                if (
                    d_candidates
                    and declared_head
                    and declared_head.endswith("t")
                    and surface_clean.endswith("t")
                    and "/t" in analysis
                ):
                    declared_homonym = declared_hom or ""
                    has_declared_match = any(
                        c.lemma == declared_head and c.homonym == declared_homonym
                        for c in d_candidates
                    )
                    if not has_declared_match and surface_candidates:
                        declared_surface_matches = [
                            c
                            for c in surface_candidates
                            if c.lemma == declared_head and c.homonym == declared_homonym
                        ]
                        if declared_surface_matches:
                            d_candidates = dedupe_entries(d_candidates + declared_surface_matches)
                            lookup_mode = "surface-fallback"
                if d_candidates:
                    if is_verb:
                        vb_only = [c for c in d_candidates if "vb" in c.pos.lower()]
                        if vb_only:
                            d_candidates = vb_only
                    elif is_noun:
                        non_vb = [c for c in d_candidates if "vb" not in c.pos.lower()]
                        if non_vb:
                            d_candidates = non_vb

            if not skip_dulat:
                if not d_candidates:
                    issues.append(
                        Issue(
                            "error",
                            str(path),
                            i,
                            line_id,
                            surface,
                            analysis,
                            "No DULAT entry found for lexeme/surface",
                        )
                    )
                else:
                    if lookup_mode == "surface-fallback":
                        issues.append(
                            Issue(
                                "warning",
                                str(path),
                                i,
                                line_id,
                                surface,
                                analysis,
                                "Lexeme parse did not match DULAT; matched by surface form",
                            )
                        )
                    # Stem presence: if DULAT has no G-stem for this verb, require a :stem marker
                    if (is_verb_global or is_deverbal) and verb_candidates_for_stem:
                        stems = set()
                        for c in verb_candidates_for_stem:
                            stems.update(entry_stems.get(c.entry_id, set()))
                        if stems and "G" not in stems and not analysis_has_stem:
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Non-G stem in DULAT requires stem marker",
                                )
                            )
                        if has_sh_stem and not ({"Š", "Št", "Špass"} & stems):
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Š stem marker present but DULAT lacks Š/Št/Špass",
                                )
                            )
                        if has_t_stem and not ({"Gt", "Št", "Dt", "Lt", "Nt"} & stems):
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Xt stem marker present but DULAT lacks *t stem",
                                )
                            )
                        if ":d" in analysis and "D" not in stems and "Dt" not in stems:
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "D stem marker present but DULAT lacks D/Dt",
                                )
                            )
                        if ":l" in analysis and "L" not in stems and "Lt" not in stems:
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "L stem marker present but DULAT lacks L/Lt",
                                )
                            )
                        if ":pass" in analysis and not ({"Špass", "Gpass", "Dpass", "N"} & stems):
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Passive stem marker present but DULAT lacks passive/N stem",
                                )
                            )

                    # POS ambiguity
                    pos_set = {c.pos for c in d_candidates if c.pos}
                    if declared_head:
                        head, hom = declared_head, (declared_hom or "")
                    else:
                        head, hom = parse_dulat_comment(raw)
                    if head:
                        pos_set = {
                            c.pos
                            for c in d_candidates
                            if c.pos and c.lemma == head and c.homonym == hom
                        }
                    if len(pos_set) > 1:
                        pos_list = ", ".join(sorted(pos_set))
                        issues.append(
                            Issue(
                                "error",
                                str(path),
                                i,
                                line_id,
                                surface,
                                analysis,
                                f"POS ambiguous in DULAT: {pos_list}",
                            )
                        )

                    # Unambiguous DULAT entry
                    if len(d_candidates) > 1 and head:
                        if not any(c.lemma == head and c.homonym == hom for c in d_candidates):
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "DULAT comment does not match candidates",
                                )
                            )
                    elif len(d_candidates) > 1 and not head:
                        cand_list = []
                        for c in d_candidates:
                            hom = f"({c.homonym})" if c.homonym else ""
                            gloss = c.gloss or "—"
                            cand_list.append(f"{c.lemma}{hom} [{c.pos}] — {gloss}")
                        msg = f"Multiple DULAT candidates for {lookup_mode}: " + "; ".join(
                            cand_list
                        )
                        issues.append(Issue("error", str(path), i, line_id, surface, analysis, msg))

                    # POS -> noun/verb ending checks
                    if head:
                        matched = [c for c in d_candidates if c.lemma == head and c.homonym == hom]
                    else:
                        matched = d_candidates
                    if matched:
                        pos_raw = matched[0].pos or ""
                        pos = pos_raw.lower()
                        is_pronoun = "pn." in pos
                        is_proper_noun = "PN" in pos_raw
                        matched_entry_ids = {m.entry_id for m in matched}
                        surface_form_morphs = {
                            (f.morph or "").lower()
                            for f in dulat_forms.get(normalize_surface(surface_clean), [])
                            if f.entry_id in matched_entry_ids and (f.morph or "").strip()
                        }
                        gender_values = {
                            (entry_gender.get(eid) or "").lower()
                            for eid in matched_entry_ids
                            if (entry_gender.get(eid) or "").strip()
                        }
                        has_f_gender = any(g.startswith("f") for g in gender_values)
                        head_lemma = (matched[0].lemma or "").strip()
                        analysis_trim = analysis.rstrip()
                        has_t_split = re.search(r"/t=?(?=\s*$|[+;,])", analysis_trim) is not None
                        has_t_plural_split = (
                            re.search(r"/t=(?=\s*$|[+;,])", analysis_trim) is not None
                        )
                        has_m_split = re.search(r"/m=?(?=\s*$|[+;,])", analysis_trim) is not None
                        surface_form_has_fem = any("f." in m for m in surface_form_morphs)
                        surface_form_has_pl = any("pl." in m for m in surface_form_morphs)
                        noun_like = not is_pronoun and (
                            is_proper_noun
                            or any(tag in pos for tag in ("n.", "dn", "gn", "tn", "mn"))
                        )
                        adjectival = "adj" in pos
                        deverbal_like = "[/" in analysis
                        pos_field_text = parts[4] if len(parts) >= 5 else ""
                        is_plurale_tantum_marked = has_plurale_tantum_note(
                            annotation_text
                        ) or has_plurale_tantum_note(pos_field_text)

                        if "vb" in pos and "[" not in analysis:
                            issues.append(
                                Issue(
                                    "error",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Verb lacks '[' ending",
                                )
                            )
                        if not is_pronoun and (
                            is_proper_noun
                            or any(tag in pos for tag in ("n.", "adj", "dn", "gn", "tn", "mn"))
                        ):
                            if "/" not in analysis:
                                issues.append(
                                    Issue(
                                        "error",
                                        str(path),
                                        i,
                                        line_id,
                                        surface,
                                        analysis,
                                        "Noun/adjective lacks '/' ending",
                                    )
                                )

                        # Gender-aware checks from DULAT metadata.
                        # For feminine singular noun forms, '/t' is the expected split ending.
                        if (
                            noun_like
                            and has_f_gender
                            and surface.endswith("t")
                            and not surface_form_has_pl
                            and not has_t_split
                            and analysis_has_missing_feminine_singular_split(
                                analysis=analysis,
                                surface=surface_clean,
                            )
                            and not analysis_has_missing_plural_split(
                                analysis=analysis,
                                surface=surface_clean,
                            )
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Feminine singular noun in DULAT should use '/t'",
                                )
                            )

                        if (
                            noun_like
                            and has_f_gender
                            and surface.endswith("t")
                            and not surface_form_has_pl
                            and declared_lemma_looks_t_final(head_lemma)
                            and has_t_split
                            and analysis_has_lexeme_t_split_without_reconstructed_t(analysis)
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Feminine noun with lexeme-final '-t' should use '(t' before '/t'",
                                )
                            )

                        # For feminine plural noun forms, '/t=' is the expected split ending.
                        if (
                            noun_like
                            and has_f_gender
                            and surface.endswith("t")
                            and surface_form_has_pl
                            and has_t_split
                            and not has_t_plural_split
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Feminine plural noun in DULAT should use '/t='",
                                )
                            )
                        if (
                            noun_like
                            and has_f_gender
                            and (not head_lemma.endswith("t"))
                            and surface.endswith("t")
                            and surface_form_has_pl
                            and not has_t_split
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Feminine plural noun in DULAT should be tagged with '/t='",
                                )
                            )
                        if (
                            (adjectival or deverbal_like)
                            and surface.endswith("t")
                            and surface_form_has_fem
                            and not has_t_split
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Feminine adjective/participle in DULAT should mark '-t' explicitly",
                                )
                            )
                        if (
                            (adjectival or deverbal_like)
                            and surface.endswith("t")
                            and surface_form_has_fem
                            and surface_form_has_pl
                            and has_t_split
                            and not has_t_plural_split
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Feminine plural adjective/participle in DULAT should use '/t='",
                                )
                            )
                        # Variant-level pl.tant. checks are only reliable on single-variant rows.
                        if (
                            noun_like
                            and is_plurale_tantum_marked
                            and "/" in analysis
                            and "+" not in analysis
                            and ";" not in analysis
                            and "," not in analysis
                            and ";" not in pos_field_text
                            and "," not in pos_field_text
                        ):
                            if surface.endswith("t") and not has_t_plural_split:
                                issues.append(
                                    Issue(
                                        "warning",
                                        str(path),
                                        i,
                                        line_id,
                                        surface,
                                        analysis,
                                        "Plurale tantum noun ending in '-t' should mark plural with '/t='",
                                    )
                                )
                            if surface.endswith("m") and not has_m_split:
                                issues.append(
                                    Issue(
                                        "warning",
                                        str(path),
                                        i,
                                        line_id,
                                        surface,
                                        analysis,
                                        "Plurale tantum noun ending in '-m' should mark plural with '/m'",
                                    )
                                )

                        # Morpheme link checks
                        morph_values = set()
                        if (matched[0].morph or "").strip():
                            morph_values.add((matched[0].morph or "").lower())
                        morph_values.update(surface_form_morphs)
                        morph = " ; ".join(sorted(morph_values))
                        if (
                            "suff" in morph and ("pn" in morph or "pers." in morph)
                        ) and "+" not in analysis:
                            lemma_letters = re.sub(
                                r"[^A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]", "", head_lemma or ""
                            )
                            if len(normalize_surface(surface_clean)) > len(
                                normalize_surface(lemma_letters)
                            ):
                                issues.append(
                                    Issue(
                                        "error",
                                        str(path),
                                        i,
                                        line_id,
                                        surface,
                                        analysis,
                                        "Suffixed pronominal form in DULAT should use '+' in analysis",
                                    )
                                )
                        # DULAT "prefc., suff." can mark finite prefix-conjugation
                        # endings (e.g., -n) rather than clitic +suffix slots.
                        if (
                            "suff." in morph
                            and "+" not in analysis
                            and "prefc." not in morph
                            and not is_plurale_tantum_marked
                            and analysis_has_missing_suffix_plus(
                                analysis=analysis,
                                surface=surface_clean,
                            )
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Suffix form without '+'",
                                )
                            )
                        if (
                            "pl." in morph
                            and surface.endswith(("m", "t"))
                            and "/" in analysis
                            and not analysis_trim.endswith(("/m", "/t", "/m=", "/t="))
                            and not is_plurale_tantum_marked
                            and analysis_has_missing_plural_split(
                                analysis=analysis,
                                surface=surface_clean,
                            )
                        ):
                            issues.append(
                                Issue(
                                    "warning",
                                    str(path),
                                    i,
                                    line_id,
                                    surface,
                                    analysis,
                                    "Plural form missing split ending",
                                )
                            )

                        # Consistency tracking by surface
                        surface_to_analyses.setdefault(surface, set()).add(analysis)
                        surface_to_ids.setdefault(surface, set()).add(line_id)
                        stem_markers = set()
                        if ":d" in analysis:
                            stem_markers.add(":d")
                        if ":l" in analysis:
                            stem_markers.add(":l")
                        if ":pass" in analysis:
                            stem_markers.add(":pass")
                        if "]š]" in analysis:
                            stem_markers.add("]š]")
                        if "]t]" in analysis:
                            stem_markers.add("]t]")
                        if stem_markers:
                            lemma_key = head or (matched[0].lemma if matched else "")
                            if lemma_key:
                                lemma_to_stems.setdefault(lemma_key, set()).update(stem_markers)
                                for marker in stem_markers:
                                    lemma_stem_ids.setdefault((lemma_key, marker), set()).add(
                                        line_id
                                    )
                                    lemma_stem_lines.setdefault((lemma_key, marker), set()).add(
                                        str(i)
                                    )

        # Alt forms in comments
        for alt in extract_alt_forms(comment):
            if "(" in alt and "&" in alt and alt.find("&") < alt.find("("):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Alt form has '&' before '('",
                    )
                )
            if has_unprefixed_reconstructed_sequence(alt):
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Alt form must prefix each reconstructed letter with '('",
                    )
                )
            if alt.count("!") % 2 != 0:
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Alt form has unpaired '!'",
                    )
                )
            for bad in ("ʕ", "ʿ", "ả", "ỉ", "ủ"):
                if bad in alt:
                    issues.append(
                        Issue(
                            "error",
                            str(path),
                            i,
                            line_id,
                            surface,
                            analysis,
                            f"Alt form has disallowed char: {bad}",
                        )
                    )
                    break
            if "ʔ" in alt and "(ʔ" not in alt:
                issues.append(
                    Issue(
                        "error",
                        str(path),
                        i,
                        line_id,
                        surface,
                        analysis,
                        "Alt form uses ʔ without preceding '('",
                    )
                )

    # Formula-sensitive homonym checks for l:
    #   tbˤ w l yṯb ilm  -> l(II) "not"
    #   idk l ytn       -> l(III) "truly/certainly"
    for idx in range(len(token_rows) - 4):
        seq = [token_rows[idx + k]["surface"] for k in range(5)]
        if seq != ["tbˤ", "w", "l", "yṯb", "ilm"]:
            continue
        l_row = token_rows[idx + 2]
        homs = extract_homonyms_for_lemma(
            l_row.get("analysis_field", ""), l_row.get("dulat_field", ""), "l"
        )
        line_no = int(l_row.get("line_no", "0") or 0)
        line_id = l_row.get("line_id", "")
        analysis_field = l_row.get("analysis_field", "")
        if "II" not in homs:
            issues.append(
                Issue(
                    "error",
                    str(path),
                    line_no,
                    line_id,
                    "l",
                    analysis_field,
                    "Formula tbˤ w l yṯb ilm expects l(II) ('not')",
                )
            )
        elif homs != {"II"}:
            issues.append(
                Issue(
                    "warning",
                    str(path),
                    line_no,
                    line_id,
                    "l",
                    analysis_field,
                    "Formula tbˤ w l yṯb ilm should use a single l(II) reading",
                )
            )

    for idx in range(len(token_rows) - 2):
        seq = [token_rows[idx + k]["surface"] for k in range(3)]
        if seq != ["idk", "l", "ytn"]:
            continue
        l_row = token_rows[idx + 1]
        homs = extract_homonyms_for_lemma(
            l_row.get("analysis_field", ""), l_row.get("dulat_field", ""), "l"
        )
        line_no = int(l_row.get("line_no", "0") or 0)
        line_id = l_row.get("line_id", "")
        analysis_field = l_row.get("analysis_field", "")
        if "III" not in homs:
            issues.append(
                Issue(
                    "error",
                    str(path),
                    line_no,
                    line_id,
                    "l",
                    analysis_field,
                    "Formula idk l ytn expects l(III) ('truly/certainly')",
                )
            )
        elif homs != {"III"}:
            issues.append(
                Issue(
                    "warning",
                    str(path),
                    line_no,
                    line_id,
                    "l",
                    analysis_field,
                    "Formula idk l ytn should use a single l(III) reading",
                )
            )

    # Long repeated sequences are usually formulaic parallels.
    # Surface-identical windows should not drift in col3-col6 payload unless
    # there is explicit reason to keep them different.
    parallel_window = 8
    parallel_occurrences: Dict[Tuple[str, ...], List[int]] = {}
    for start in range(len(token_rows) - parallel_window + 1):
        window = token_rows[start : start + parallel_window]
        surfaces = tuple((row.get("surface", "") or "").strip() for row in window)
        if not all(surfaces):
            continue
        if any("x" in s.lower() for s in surfaces):
            continue
        if (surfaces[0] or "").lower() in {"d", "w", "l", "b", "m", "n", "p"}:
            continue
        # Reduce noise from high-frequency function-word chains.
        lexical_slots = 0
        for s in surfaces:
            letters = re.sub(r"[^A-Za-zˤḫṣṯẓġḏḥṭš]", "", s)
            if len(letters) >= 2:
                lexical_slots += 1
        if lexical_slots < 4:
            continue
        parallel_occurrences.setdefault(surfaces, []).append(start)

    for surfaces, starts in parallel_occurrences.items():
        if len(starts) <= 1:
            continue
        payload_to_spans: Dict[Tuple[Tuple[str, str, str, str], ...], List[Tuple[str, str]]] = {}
        for start in starts:
            window = token_rows[start : start + parallel_window]
            payload = tuple(
                (
                    (row.get("analysis_field", "") or "").strip(),
                    (row.get("dulat_field", "") or "").strip(),
                    (row.get("pos_field", "") or "").strip(),
                    (row.get("gloss_field", "") or "").strip(),
                )
                for row in window
            )
            span = (window[0].get("line_id", ""), window[-1].get("line_id", ""))
            payload_to_spans.setdefault(payload, []).append(span)
        if len(payload_to_spans) <= 1:
            continue
        span_parts = []
        for spans in payload_to_spans.values():
            ids = [f"{a}-{b}" if a and b else (a or b) for a, b in spans]
            span_parts.append(",".join(ids))
        surface_key = " ".join(surfaces)
        issues.append(
            Issue(
                "info",
                str(path),
                0,
                "",
                surface_key,
                "",
                "Repeated 8-token surface sequence has inconsistent col3-col6 payload across parallels: "
                + " ; ".join(span_parts),
            )
        )

    # Consistency checks
    # Group ids by analysis variant per surface for easier review
    for surface, analyses in surface_to_analyses.items():
        if len(analyses) > 1:
            variant_map: Dict[str, List[str]] = {}
            for line_id, (srf, analysis) in seen_pairs:
                if srf != surface:
                    continue
                variant_map.setdefault(analysis.strip(), []).append(line_id)
            parts = []
            for analysis in sorted(variant_map.keys()):
                ids = ",".join(sorted(set(variant_map[analysis])))
                parts.append(f"{analysis} (ids: {ids})")
            issues.append(
                Issue(
                    "info",
                    str(path),
                    0,
                    "",
                    surface,
                    "",
                    f"Surface {surface} parsed inconsistently: " + "; ".join(parts),
                )
            )
    for lemma, stems in lemma_to_stems.items():
        if len(stems) > 1:
            marker_ids = {m: lemma_stem_ids.get((lemma, m), set()) for m in stems}
            all_ids = set().union(*marker_ids.values()) if marker_ids else set()
            # If all markers occur only within the same single id, it's acceptable (multiple infixes in one verb)
            if len(all_ids) <= 1:
                continue
            # If all markers occur on the same set of ids, it's still consistent enough; warn only if they differ
            id_sets = list(marker_ids.values())
            if id_sets and all(s == id_sets[0] for s in id_sets):
                continue

            parts = []
            for marker in sorted(stems):
                ids = ",".join(sorted(marker_ids.get(marker, set())))
                lines = ",".join(sorted(lemma_stem_lines.get((lemma, marker), set())))
                parts.append(f"{marker} (ids: {ids}; lines: {lines})")
            issues.append(
                Issue(
                    "warning",
                    str(path),
                    0,
                    "",
                    "",
                    "",
                    f"Lemma {lemma} has multiple stem markers: " + "; ".join(parts),
                )
            )

    return issues


# -----------------------------
# HTML
# -----------------------------


def render_html(issues: List[Issue], out_path: Path):
    rows = []
    for it in issues:
        rows.append(
            f"<tr class='{it.level}'>"
            f"<td>{html.escape(it.level)}</td>"
            f"<td>{html.escape(it.file)}</td>"
            f"<td>{it.line_no}</td>"
            f"<td>{html.escape(it.line_id)}</td>"
            f"<td>{html.escape(it.surface)}</td>"
            f"<td>{html.escape(it.analysis)}</td>"
            f"<td>{html.escape(it.message)}</td>"
            f"</tr>"
        )

    body = "\n".join(rows) if rows else "<tr><td colspan='7'>No issues</td></tr>"

    html_text = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Morphology Lint Report</title>
<style>
body {{ font-family: Arial, sans-serif; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 4px 6px; font-size: 12px; }}
tr.error {{ background: #ffe5e5; }}
tr.warning {{ background: #fff3cd; }}
tr.info {{ background: #e8f4ff; }}
</style>
</head>
<body>
<h1>Morphology Lint Report</h1>
<table>
<thead>
<tr>
<th>Level</th><th>File</th><th>Line</th><th>ID</th><th>Surface</th><th>Analysis</th><th>Message</th>
</tr>
</thead>
<tbody>
{body}
</tbody>
</table>
</body>
</html>
"""
    out_path.write_text(html_text, encoding="utf-8")


# -----------------------------
# CLI
# -----------------------------


def main():
    parser = argparse.ArgumentParser(description="Morphology linter")
    parser.add_argument(
        "files",
        nargs="+",
        help="Input labeled files (.txt) or raw CUC tablet files (.tsv)",
    )
    parser.add_argument("--html", help="Write HTML report to file")
    parser.add_argument(
        "--dulat", default="sources/dulat_cache.sqlite", help="Path to DULAT sqlite"
    )
    parser.add_argument("--udb", default="sources/udb_cache.sqlite", help="Path to UDB sqlite")
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Run only checks that do not require DULAT/UDB sqlite databases",
    )
    parser.add_argument(
        "--input-format",
        choices=["auto", "labeled", "cuc_tablets_tsv"],
        default="auto",
        help="Input row format: auto-detect, fully labeled files, or raw cuc_tablets_tsv rows",
    )
    args = parser.parse_args()

    if args.no_db:
        dulat_forms = {}
        entry_meta = {}
        lemma_map = {}
        entry_stems = {}
        entry_gender = {}
        udb_words = None
    else:
        dulat_forms, entry_meta, lemma_map, entry_stems, entry_gender = load_dulat(Path(args.dulat))
        udb_words = load_udb_words(Path(args.udb)) if Path(args.udb).exists() else None

    all_issues: List[Issue] = []

    for file_path in args.files:
        fpath = Path(file_path)
        if not fpath.exists():
            print(f"File not found: {file_path}", file=sys.stderr)
            continue
        baseline = None
        if fpath.name.endswith(".txt"):
            candidate = fpath.with_name(fpath.stem + "_original.txt")
            if candidate.exists():
                baseline = candidate
        issues = lint_file(
            fpath,
            dulat_forms,
            entry_meta,
            lemma_map,
            entry_stems,
            entry_gender,
            udb_words,
            baseline,
            input_format=args.input_format,
            db_checks=(not args.no_db),
        )
        all_issues.extend(issues)

    # CLI output
    levels = {"error": 0, "warning": 1, "info": 2}
    all_issues.sort(key=lambda x: (levels.get(x.level, 9), x.file, x.line_no))

    if args.html:
        render_html(all_issues, Path(args.html))
        print(f"HTML report written to {args.html}")
    else:
        for it in all_issues:
            loc = f"{it.file}:{it.line_no}" if it.line_no else it.file
            print(f"{it.level.upper()} {loc} {it.line_id} {it.surface} {it.message}")

        print(f"Total issues: {len(all_issues)}")


if __name__ == "__main__":
    main()
