#!/usr/bin/env python3
# ruff: noqa: E402, I001
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
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dulat_patches import load_dulat_entry_patches  # noqa: E402
from project_paths import get_project_paths  # noqa: E402
from pipeline.config.dulat_entry_forms_fallback import extract_forms_from_entry_text  # noqa: E402
from pipeline.config.dulat_form_morph_overrides import override_dulat_form_morphology  # noqa: E402
from pipeline.config.dulat_form_text_overrides import expand_dulat_form_texts  # noqa: E402
from pipeline.dulat_attestation_index import DulatAttestationIndex  # noqa: E402
from pipeline.dulat_attestation_translation_index import (  # noqa: E402
    DulatAttestationTranslationIndex,
)

SEPARATOR_RE = re.compile(
    r"^\s*#\s*(?:-+\s*)?(?:KTU|CAT)\s+(\d+\.\d+)"
    r"(?:\s+([IVX]+):(\d+)|:(\d+)|\s+(\d+))\s*$",
    re.IGNORECASE,
)

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
_PREFORMATIVE_LETTERS = {"y", "t", "a", "n", "i", "u"}
_REDIRECT_TARGET_RE = re.compile(r"<i>([^<]+)</i>", re.IGNORECASE)
_REDIRECT_SLASH_TARGET_RE = re.compile(r"/[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ-]+/")
_L_STEM_MORPH_RE = re.compile(r"\b(L|Lt|tL)\b")
_SENSE_CITATION_RE = re.compile(
    r"\b(?:KTU|CAT)?\s*\d+\.\d+(?:\s+[IVX]+)?\s*:\s*\d+(?:\s*[–-]\s*\d+)?\b",
    re.IGNORECASE,
)
_SENSE_CROSSREF_RE = re.compile(r"\bcf\.\b", re.IGNORECASE)
_BASE_NOMINAL_ANALYSIS_RE = re.compile(
    r"^(?P<lemma>[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ]+)(?P<hom>\([IVX]+\))?/$"
)

# Automatic parsing is a ranked review aid, not a single-best-answer tagger.
# Keep a small bundle of linguistically viable alternatives while excluding
# low-scoring derived hypotheses that would make every token needlessly noisy.
AUTOMATIC_MAX_VARIANTS = 5
VIABLE_DERIVED_SCORE_WINDOW = 6
VIABLE_EXACT_SCORE_WINDOW = 7
VIABLE_SPLIT_SCORE_WINDOW = 8


def format_preformative_marker(letter: str) -> str:
    """Render canonical prefix-conjugation marker for one preformative letter."""
    preformative = (letter or "").strip()
    if preformative in {"a", "i", "u"}:
        return f"!(ʔ&{preformative}!"
    return f"!{preformative}!"


@dataclass(frozen=True)
class Entry:
    entry_id: int
    lemma: str
    hom: str
    pos: str
    gloss: str
    wiki_tr: str
    stem_glosses: Dict[str, str] = field(default_factory=dict)
    redirect_targets: Tuple[str, ...] = ()


@dataclass
class Variant:
    entries: Tuple[Entry, ...]
    base_surface: str
    score: int = 0
    from_redirect: bool = False


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
    # Keep first concise segment, but do not split on commas inside parentheses.
    g = _split_first_top_level(g, sep=",")[0]
    g = g.strip(" ,;")
    # keep compact first chunk when automated extraction is noisy
    if len(g) > 110:
        g = g[:110].rsplit(" ", 1)[0].strip(" ,;")
    return g


def normalize_reference_sense_gloss(s: str) -> str:
    """Normalize sense-label casing for rendered TSV glosses.

    DULAT sense definitions for non-verbal entries are often title-cased labels
    like `Hero` or `Man, husband`. In TSV output we keep the usual lowercase
    gloss style unless the sense begins with an all-caps token or explicit
    markup-like punctuation.
    """
    value = strip_html(s)
    if not value:
        return ""
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    value = value.replace(";", ",")
    value = value.replace('"', "")
    value = _split_first_top_level(value, sep=",")[0]
    value = value.strip(" ,;")
    if not value:
        return ""
    prefix_match = re.match(r"^(?P<prefix>\d+\)\s+)?(?P<rest>.*)$", value)
    prefix = prefix_match.group("prefix") or "" if prefix_match else ""
    rest = prefix_match.group("rest") or value if prefix_match else value
    letter_match = re.match(r"^(?P<head>[^A-Za-z]*)(?P<word>[A-Za-z]+)(?P<tail>.*)$", rest)
    if letter_match:
        word = letter_match.group("word")
        if not (len(word) > 1 and word.isupper()):
            rest = (
                letter_match.group("head")
                + word[:1].lower()
                + word[1:]
                + letter_match.group("tail")
            )
        return f"{prefix}{rest}".strip()
    return value


def is_usable_sense_definition(definition: str) -> bool:
    """Return False for sense rows that are attestational examples/cross-refs."""
    text = strip_html(definition or "")
    if not text:
        return False
    if _SENSE_CROSSREF_RE.search(text):
        return False
    if _SENSE_CITATION_RE.search(text):
        return False
    return True


def _split_first_top_level(text: str, sep: str = ",") -> Tuple[str, str]:
    """Split on first separator not nested in parentheses/brackets."""
    depth_round = 0
    depth_square = 0
    for idx, ch in enumerate(text):
        if ch == "(":
            depth_round += 1
            continue
        if ch == ")" and depth_round > 0:
            depth_round -= 1
            continue
        if ch == "[":
            depth_square += 1
            continue
        if ch == "]" and depth_square > 0:
            depth_square -= 1
            continue
        if ch == sep and depth_round == 0 and depth_square == 0:
            return text[:idx], text[idx + 1 :]
    return text, ""


def extract_redirect_targets(summary: str, text: str) -> Tuple[str, ...]:
    source = " ".join(part for part in (summary or "", text or "") if part)
    if not source:
        return ()

    cf_match = re.search(r"\bcf\.\s*(.*)$", source, flags=re.IGNORECASE)
    scope = cf_match.group(1) if cf_match else source
    scope = re.split(r"(?:<br\s*/?>|[.;])", scope, maxsplit=1, flags=re.IGNORECASE)[0]

    out: List[str] = []
    for token in _REDIRECT_TARGET_RE.findall(scope):
        cleaned = strip_html(token).strip()
        cleaned = re.sub(r"[.,;:!?]+$", "", cleaned).strip()
        if cleaned:
            out.append(cleaned)

    for token in _REDIRECT_SLASH_TARGET_RE.findall(scope):
        cleaned = token.strip()
        if cleaned:
            out.append(cleaned)

    if not out:
        plain_scope = strip_html(scope)
        m = re.search(r"([A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ][A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ-]*)", plain_scope)
        if m:
            out.append(m.group(1))

    if not out:
        return ()
    return tuple(dict.fromkeys(out))


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
    tablet = m.group(1)
    if m.group(2) and m.group(3):
        col = m.group(2).upper()
        ln = m.group(3)
        return f"CAT {tablet} {col}:{ln}"
    ln = m.group(4) or m.group(5)
    if ln:
        return f"CAT {tablet}:{ln}"
    return None


def tablet_id_from_ref(ref: str) -> str:
    m = re.search(r"CAT\s+(\d+\.\d+)", ref or "")
    return m.group(1) if m else ""


_REF_LINE_RE = re.compile(r"^(?P<head>.+:)(?P<line>\d+)$")


def mentions_for_ref(
    reverse_mentions: Dict[str, Set[int]],
    ref: str,
    line_tolerance: int = 1,
) -> Set[int]:
    """Return reverse mentions for a line ref, tolerating small line shifts.

    DULAT citations can be offset by one line from the CUC numbering (e.g.
    DULAT '1.5 IV 2' = CUC IV:3 throughout KTU 1.5 col. IV). Exact-line
    mentions always win; only when the exact lookup is empty are mentions of
    the +-``line_tolerance`` neighbouring lines returned as a fallback.

    Args:
        reverse_mentions: canonical ref -> DULAT entry ids.
        ref: canonical line ref (``CAT 1.5 IV:2``).
        line_tolerance: maximum line distance for the fallback; 0 disables it.

    Returns:
        Entry ids cited for the line, or for its nearest neighbours when the
        line itself has none.
    """
    exact = reverse_mentions.get(ref, set())
    if exact or line_tolerance <= 0:
        return set(exact)
    m = _REF_LINE_RE.match(ref or "")
    if not m:
        return set()
    head = m.group("head")
    line_no = int(m.group("line"))
    nearby: Set[int] = set()
    for offset in range(1, line_tolerance + 1):
        for neighbour in (line_no - offset, line_no + offset):
            if neighbour < 1:
                continue
            nearby.update(reverse_mentions.get(f"{head}{neighbour}", set()))
        if nearby:
            break
    return nearby


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


def takes_nominal_slash(pos: str) -> bool:
    raw = pos or ""
    p = raw.lower()
    return bool(
        re.search(r"\bn\.", p)
        or re.search(r"\badj\.?", p)
        or any(tag in raw for tag in ("DN", "PN", "RN", "TN", "GN", "MN"))
    )


def extract_letters(text: str) -> str:
    return "".join(ch for ch in (text or "") if LETTER_RE.match(ch))


def lemma_to_letters(lemma: str, fallback: str = "") -> str:
    lm = (lemma or "").strip()
    if not lm:
        return normalize_analysis(extract_letters(fallback))

    if lm.startswith("/") and lm.endswith("/"):
        body = re.sub(r"\([^)]*\)", "", lm[1:-1])
        # A slash inside a root separates alternative radicals of one slot
        # (/y/w-ḥ-l/ = y-ḥ-l or w-ḥ-l). Prefer the alternative whose letters
        # occur in the observed surface; default to the first one.
        fallback_letters = normalize_analysis(extract_letters(fallback))
        radicals = []
        for slot in body.split("-"):
            alternatives = [alt for alt in slot.split("/") if alt] or [slot]
            chosen = alternatives[0]
            if len(alternatives) > 1 and fallback_letters:
                for alt in alternatives:
                    alt_letters = normalize_analysis(extract_letters(alt))
                    if alt_letters and alt_letters in fallback_letters:
                        chosen = alt
                        break
            radicals.append(chosen)
        letters = extract_letters("".join(radicals))
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


def prefixed_verb_match(
    surface_plain: str,
    stem_plain: str,
    stem_marker_plain: str = "",
) -> Optional[Tuple[str, int]]:
    """Return (tail, hidden_stem_letters) for prefixed-verb matching.

    The matcher checks both plain stem (`qtl`) and stem-marker + stem (`šqtl`,
    `štqtl`) realizations against the post-preformative surface body.
    """
    if not surface_plain or not stem_plain:
        return None
    if surface_plain[0] not in _PREFORMATIVE_LETTERS:
        return None
    body = surface_plain[1:]
    if not body:
        return None

    candidates: List[Tuple[str, int]] = []
    if stem_marker_plain:
        candidates.append((stem_marker_plain + stem_plain, len(stem_marker_plain)))
    candidates.append((stem_plain, 0))

    for candidate, marker_len in candidates:
        if body.startswith(candidate):
            return body[len(candidate) :], 0

    for candidate, marker_len in candidates:
        if candidate.startswith(body):
            visible_stem_letters = max(0, len(body) - marker_len)
            hidden_stem_letters = max(0, len(stem_plain) - visible_stem_letters)
            return "", hidden_stem_letters

    return None


def mark_hidden_terminal_stem_letters(stem: str, hidden_count: int) -> str:
    """Prefix '(' on hidden terminal stem letters in contracted prefix forms."""
    if hidden_count <= 0:
        return stem

    letter_indices = [idx for idx, ch in enumerate(stem) if LETTER_RE.match(ch)]
    if not letter_indices:
        return stem
    hidden_indices = set(letter_indices[-hidden_count:])

    out: List[str] = []
    for idx, ch in enumerate(stem):
        if idx in hidden_indices and (idx == 0 or stem[idx - 1] != "("):
            out.append("(")
        out.append(ch)
    return "".join(out)


def mark_reconstructed_prefix_letters(form: str, prefix_letters: int) -> str:
    """Prefix '(' before the first `prefix_letters` lexical letters."""
    if prefix_letters <= 0:
        return form
    out: List[str] = []
    remaining = prefix_letters
    for ch in form:
        if remaining > 0 and LETTER_RE.match(ch):
            out.append("(")
            out.append(ch)
            remaining -= 1
            continue
        out.append(ch)
    return "".join(out)


def is_n_weak_iii_aleph_root(lemma: str) -> bool:
    """Return True for lexical roots of the shape /n-...-ʔ/."""
    lm = (lemma or "").strip()
    if not (lm.startswith("/") and lm.endswith("/")):
        return False
    parts = [part for part in lm[1:-1].split("-") if part]
    return len(parts) == 3 and parts[0] == "n" and parts[2] == "ʔ"


def is_iii_aleph_root(lemma: str) -> bool:
    """Return True for lexical roots with final aleph (e.g. /q-r-ʔ/, /b-ʔ/)."""
    lm = (lemma or "").strip()
    if not (lm.startswith("/") and lm.endswith("/")):
        return False
    parts = [part for part in lm[1:-1].split("-") if part]
    return len(parts) >= 2 and parts[-1] == "ʔ"


def has_prefix_morphology(morph_values: Sequence[str]) -> bool:
    merged = " | ".join(morph_values or []).lower()
    return "prefc." in merged


def has_n_suffix_morphology(morph_values: Sequence[str]) -> bool:
    """Return whether DULAT identifies an N-stem suffix-conjugation form."""
    merged = " | ".join(morph_values or [])
    return bool(re.search(r"(?:^|[,|;]\s*)N(?:\s*[,|;]|\s+)", merged)) and (
        "suffc." in merged.lower()
    )


def has_l_stem_morphology(morph_values: Sequence[str]) -> bool:
    merged = " | ".join(morph_values or [])
    return bool(_L_STEM_MORPH_RE.search(merged))


def maybe_expand_l_stem_terminal_gemination(
    stem: str,
    surface_plain: str,
    stem_marker: str,
    morph_values: Sequence[str],
) -> str:
    """Expand L-stem terminal gemination when surface shows doubled radical.

    DULAT roots like /q-ṭ(-ṭ)/ are normalized to `qṭ` by lemma parsing, while
    L-stem forms surface as `qṭṭ`. Keep the doubled radical in the stem body
    (before `[`) instead of leaving it in the tail.
    """
    if not has_l_stem_morphology(morph_values):
        return stem
    stem_plain = extract_letters(stem)
    if len(stem_plain) < 2:
        return stem
    last_radical = stem_plain[-1]
    if stem_plain.endswith(last_radical * 2):
        return stem

    marker_plain = extract_letters(stem_marker)
    surface_body = (
        surface_plain[1:]
        if surface_plain and surface_plain[0] in _PREFORMATIVE_LETTERS
        else surface_plain
    )
    if not surface_body:
        return stem

    if marker_plain and surface_body.startswith(f"{marker_plain}{stem_plain}{last_radical}"):
        return stem + last_radical
    if surface_body.startswith(f"{stem_plain}{last_radical}"):
        return stem + last_radical
    return stem


def build_prefixed_iii_aleph_analysis(
    surface_plain: str,
    stem: str,
    hom: str,
    stem_marker: str,
    restore_initial_n: bool = False,
) -> Optional[str]:
    """Encode contracted prefix forms for III-aleph roots.

    Example:
    - tḫṭu -> !t!ḫṭ(ʔ[&u
    - yšu  -> !y!(nš(ʔ[&u
    """
    if not surface_plain or surface_plain[0] not in _PREFORMATIVE_LETTERS:
        return None
    body = surface_plain[1:]
    if not body:
        return None
    m = re.search(r"[aiu]", body)
    if not m:
        return None

    inflection = body[m.start() :]
    visible_stem = body[: m.start()]
    stem_plain = extract_letters(stem)
    if not stem_plain:
        return None

    expected_visible = stem_plain
    if restore_initial_n and expected_visible.startswith("n"):
        expected_visible = expected_visible[1:]
    if expected_visible.endswith("ʔ"):
        expected_visible = expected_visible[:-1]
    if visible_stem and expected_visible and not expected_visible.startswith(visible_stem):
        return None

    normalized_stem = stem
    if restore_initial_n:
        if normalized_stem.startswith("n"):
            normalized_stem = "(n" + normalized_stem[1:]
        elif not normalized_stem.startswith("(n"):
            normalized_stem = "(n" + normalized_stem

    if normalized_stem.endswith("ʔ"):
        normalized_stem = normalized_stem[:-1] + "(ʔ"
    else:
        aleph_idx = normalized_stem.rfind("ʔ")
        if aleph_idx >= 0 and (aleph_idx == 0 or normalized_stem[aleph_idx - 1] != "("):
            normalized_stem = normalized_stem[:aleph_idx] + "(ʔ" + normalized_stem[aleph_idx + 1 :]

    marker = format_preformative_marker(surface_plain[0])
    return f"{marker}{stem_marker}{normalized_stem}{hom}[&{inflection}"


def build_prefixed_n_weak_iii_aleph_analysis(
    surface_plain: str,
    stem: str,
    hom: str,
    stem_marker: str,
) -> Optional[str]:
    """Encode contracted prefix forms for /n-...-ʔ/ roots.

    Example:
    - yšu -> !y!(nš(ʔ[&u
    - tšan -> !t!(nš(ʔ[&an
    """
    if not surface_plain or surface_plain[0] not in _PREFORMATIVE_LETTERS:
        return None
    body = surface_plain[1:]
    if not body:
        return None
    m = re.search(r"[aiu]", body)
    if not m:
        return None

    inflection = body[m.start() :]
    normalized_stem = stem
    if body.startswith("n"):
        # The root-initial n is written on the tablet (tnšan): keep it
        # visible instead of wrapping it as a hidden '(n'.
        pass
    elif normalized_stem.startswith("n"):
        normalized_stem = "(n" + normalized_stem[1:]
    elif not normalized_stem.startswith("(n"):
        normalized_stem = "(n" + normalized_stem

    if normalized_stem.endswith("ʔ"):
        normalized_stem = normalized_stem[:-1] + "(ʔ"
    else:
        aleph_idx = normalized_stem.rfind("ʔ")
        if aleph_idx >= 0 and (aleph_idx == 0 or normalized_stem[aleph_idx - 1] != "("):
            normalized_stem = normalized_stem[:aleph_idx] + "(ʔ" + normalized_stem[aleph_idx + 1 :]

    marker = format_preformative_marker(surface_plain[0])
    return f"{marker}{stem_marker}{normalized_stem}{hom}[&{inflection}"


def build_prefixed_weak_fallback_analysis(
    *,
    surface_plain: str,
    stem_plain: str,
    stem_marker: str,
    hom: str,
) -> Optional[str]:
    """Build reconstructable fallback for prefixed verbs when direct match fails.

    Handles recurrent classes:
    - weak-final y/w showing surface -n in prefc. forms
    - weak-initial h elision after preformative
    - I-aleph and II-aleph vowel realization in prefix forms
    """
    if not surface_plain or not stem_plain:
        return None
    preformative = surface_plain[0]
    if preformative not in _PREFORMATIVE_LETTERS:
        return None
    body = surface_plain[1:]
    if not body:
        return None

    marker = format_preformative_marker(preformative)

    # Weak-final roots: surface keeps n where root has terminal y/w.
    if stem_plain.endswith(("y", "w")) and body.startswith(stem_plain[:-1]):
        tail = body[len(stem_plain) - 1 :]
        host = f"{stem_plain[:-1]}({stem_plain[-1]}"
        return f"{marker}{stem_marker}{host}{hom}[{tail}"

    # Weak-initial h can drop in prefixed forms (e.g. /h-l-k/ -> ylkn).
    if stem_plain.startswith("h") and len(stem_plain) > 1 and body.startswith(stem_plain[1:]):
        tail = body[len(stem_plain) - 1 :]
        host = f"(h{stem_plain[1:]}"
        return f"{marker}{stem_marker}{host}{hom}[{tail}"

    # I-aleph roots: aleph realized via vowel after preformative.
    if (
        stem_plain.startswith("ʔ")
        and body[0] in {"a", "i", "u"}
        and body[1:].startswith(stem_plain[1:])
    ):
        tail = body[len(stem_plain) :]
        host = f"(ʔ&{body[0]}{stem_plain[1:]}"
        return f"{marker}{stem_marker}{host}{hom}[{tail}"

    # II-aleph roots: middle aleph realized via vowel.
    if (
        len(stem_plain) >= 3
        and stem_plain[1] == "ʔ"
        and body.startswith(stem_plain[0])
        and len(body) >= 3
        and body[1] in {"a", "i", "u"}
        and body[2:].startswith(stem_plain[2:])
    ):
        tail = body[len(stem_plain) :]
        host = f"{stem_plain[0]}(ʔ&{body[1]}{stem_plain[2:]}"
        return f"{marker}{stem_marker}{host}{hom}[{tail}"

    return None


_VOWEL_LETTERS = {"a", "i", "u"}


def analysis_reconstructs(surface: str, analysis: str) -> bool:
    """Return True when the analysis decodes exactly to the surface letters."""
    from linter.lint import (
        ANALYSIS_SURFACE_LETTER_RE,
        normalize_surface,
        reconstruct_surface_from_analysis,
    )

    letters = "".join(ch for ch in (surface or "") if ANALYSIS_SURFACE_LETTER_RE.match(ch))
    expected = normalize_surface(letters or (surface or "").strip())
    reconstructed = normalize_surface(reconstruct_surface_from_analysis((analysis or "").strip()))
    return bool(expected) and reconstructed == expected


_WEAK_INITIAL_RADICALS = {"y", "n", "l", "w"}


def build_hidden_initial_radical_analysis(
    *,
    surface_plain: str,
    stem_plain: str,
    stem_marker: str,
    hom: str,
) -> Optional[str]:
    """Hide an unwritten weak/assimilating first radical with '('.

    ttn -> !t!(ytn[, tdd -> !t!(ndd[, dˤ -> (ydˤ[ per Tagging conventions
    (assimilated n and weak-initial y/w/l are added by means of '(').
    """
    if len(stem_plain) < 2 or stem_plain[0] not in _WEAK_INITIAL_RADICALS:
        return None
    rest = stem_plain[1:]
    host = f"({stem_plain[0]}{rest}"
    if surface_plain.startswith(rest):
        tail = surface_plain[len(rest) :]
        return f"{stem_marker}{host}{hom}[{tail}"
    if surface_plain[:1] in _PREFORMATIVE_LETTERS and surface_plain[1:].startswith(rest):
        marker = format_preformative_marker(surface_plain[0])
        tail = surface_plain[len(rest) + 1 :]
        return f"{marker}{stem_marker}{host}{hom}[{tail}"
    return None


def build_aligned_nominal_analysis(
    *,
    surface_plain: str,
    lex_plain: str,
    hom: str,
) -> Optional[str]:
    """Align a nominal surface against its lexeme letters with (/& marks.

    Attested-form spellings that differ from the lexeme by at most two local
    edits are encoded mechanically: lexeme-only letters get '(', surface-only
    letters get '&' (adjacent pairs form substitutions), and surface material
    after the last lexeme letter goes behind the '/' closure as ending:
    bht -> b&ht/, mat -> m(i&at/, ˤqšr -> (a&ˤqšr/, rpum -> rpu/m.
    """
    if not lex_plain or not surface_plain or surface_plain == lex_plain:
        return None
    tail = ""
    body = surface_plain
    # Peel trailing nominal-ending material (plural m / feminine t) so it
    # lands after the '/' closure; other surface-only tails stay before the
    # closure as '&' letters (qdqdh -> qdqd&h/, per existing convention).
    while (
        body
        and body[-1] in {"m", "t"}
        and lex_plain
        and not lex_plain.endswith(body[-1])
        and body[:-1].startswith(lex_plain[: len(body) - 1])
    ):
        if lex_plain.startswith(body[:-1]) or body[:-1] == lex_plain:
            tail = body[-1] + tail
            body = body[:-1]
        else:
            break
    if body == lex_plain:
        return f"{lex_plain}{hom}/{tail}"
    if body.startswith(lex_plain):
        # Pure extensions of the lexeme are suffix/clitic material owned by
        # the legacy tail logic and the suffix-split machinery.
        return None

    # Minimal-edit alignment between lexeme and (tail-less) surface body.
    edits: List[Tuple[str, str]] = []  # (op, letter): keep|hide|extra
    i = j = 0
    ops = 0
    while i < len(lex_plain) and j < len(body):
        if lex_plain[i] == body[j]:
            edits.append(("keep", lex_plain[i]))
            i += 1
            j += 1
        elif (
            lex_plain[i : i + 1]
            and body[j : j + 1]
            and lex_plain[i + 1 :].startswith(body[j + 1 :])
        ):
            edits.append(("hide", lex_plain[i]))
            edits.append(("extra", body[j]))
            i += 1
            j += 1
            ops += 1
        elif lex_plain[i + 1 :].startswith(body[j:]):
            edits.append(("hide", lex_plain[i]))
            i += 1
            ops += 1
        elif body[j + 1 :].startswith(lex_plain[i:]):
            edits.append(("extra", body[j]))
            j += 1
            ops += 1
        else:
            return None
    for letter in lex_plain[i:]:
        edits.append(("hide", letter))
        ops += 1
    for letter in body[j:]:
        edits.append(("extra", letter))
        ops += 1
    kept = sum(1 for op, _letter in edits if op == "keep")
    min_kept = 1 if len(lex_plain) <= 2 else 2
    if ops > 2 or kept < min_kept or (kept <= ops and kept >= 2) or (kept == 1 and ops > 1):
        return None
    encoded = "".join(
        letter if op == "keep" else ("(" + letter if op == "hide" else "&" + letter)
        for op, letter in edits
    )
    # Homonym labels belong to the lexical host, before any trailing
    # surface-only editorial signs (sp[[x]]r[[n]] -> sp&xr(II)&n/).
    trailing_extra = re.search(r"(?:&[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ])+$", encoded)
    if hom and trailing_extra:
        encoded = (
            encoded[: trailing_extra.start()]
            + hom
            + encoded[trailing_extra.start() :]
        )
        hom = ""
    return f"{encoded}{hom}/{tail}"


def build_s_stem_assimilation_analysis(
    *,
    surface_plain: str,
    stem: str,
    stem_plain: str,
    stem_marker_plain: str,
    hom: str,
) -> Optional[str]:
    """Encode Š-augment assimilated to a following ṯ as ](š&ṯ].

    DULAT /ṯ-b/ attests Š prefc. tṯṯb/yṯṯb/tṯṯbn, impv. ṯṯb, inf. ṯṯb: the
    augment š is written ṯ before the ṯ-initial root.
    """
    if stem_marker_plain != "š" or not stem_plain.startswith("ṯ"):
        return None
    if surface_plain.startswith("ṯ" + stem_plain):
        tail = surface_plain[len(stem_plain) + 1 :]
        return f"](š&ṯ]{stem}{hom}[{tail}"
    if surface_plain[:1] in _PREFORMATIVE_LETTERS and surface_plain[1:].startswith(
        "ṯ" + stem_plain
    ):
        marker = format_preformative_marker(surface_plain[0])
        tail = surface_plain[len(stem_plain) + 2 :]
        return f"{marker}](š&ṯ]{stem}{hom}[{tail}"
    return None


def build_aleph_realization_analysis(
    *,
    surface_plain: str,
    stem_plain: str,
    stem_marker: str,
    hom: str,
) -> Optional[str]:
    """Encode aleph radicals realized as vowel letters ((ʔ&V pattern).

    Covers all three root positions, with or without a preformative:
    likt -> l(ʔ&ik[t (II-ʔ), iḫdn -> (ʔ&iḫd[n (I-ʔ),
    tnšan -> !t!nš(ʔ&a[n (III-ʔ).
    """

    def _attempt(body: str, marker: str) -> Optional[str]:
        if not body:
            return None
        if (
            stem_plain.startswith("ʔ")
            and body[:1] in _VOWEL_LETTERS
            and body[1:].startswith(stem_plain[1:])
        ):
            tail = body[len(stem_plain) :]
            return f"{marker}{stem_marker}(ʔ&{body[0]}{stem_plain[1:]}{hom}[{tail}"
        if (
            len(stem_plain) >= 3
            and stem_plain[1] == "ʔ"
            and body[:1] == stem_plain[0]
            and body[1:2] in _VOWEL_LETTERS
            and body[2:].startswith(stem_plain[2:])
        ):
            tail = body[len(stem_plain) :]
            return f"{marker}{stem_marker}{stem_plain[0]}(ʔ&{body[1]}{stem_plain[2:]}{hom}[{tail}"
        # Unprefixed n-weak III-ʔ forms (impv. ša/šu of /n-š-ʔ/): hidden
        # initial n and final ʔ, vocalization after '[' per the conventions.
        if (
            len(stem_plain) >= 3
            and stem_plain.startswith("n")
            and stem_plain.endswith("ʔ")
            and body[:-1] == stem_plain[1:-1]
            and body[-1:] in _VOWEL_LETTERS
        ):
            mid = stem_plain[1:-1]
            return f"{marker}{stem_marker}(n{mid}(ʔ{hom}[&{body[-1]}"
        # Other III-ʔ realization is owned by the prefixed III-aleph
        # builders, which place the vocalization after '[' likewise.
        return None

    direct = _attempt(surface_plain, "")
    if direct is not None:
        return direct
    if surface_plain[:1] in _PREFORMATIVE_LETTERS and len(surface_plain) > 1:
        return _attempt(surface_plain[1:], format_preformative_marker(surface_plain[0]))
    return None


def build_n_suffix_analysis(
    *,
    surface_plain: str,
    stem_plain: str,
    hom: str,
) -> Optional[str]:
    """Encode a written N-stem formative in a suffix-conjugation form.

    DULAT morphology, rather than the presence of surface ``n``, gates this
    builder.  The initial written formative is therefore ``]n]``.  A final
    aleph realized by a vowel letter keeps the radical reconstructed and the
    written vowel after the verbal ``[`` closure: nḫtu -> ]n]ḫt(ʔ[&u.
    """
    if not surface_plain.startswith("n") or not stem_plain:
        return None
    body = surface_plain[1:]
    if (
        stem_plain.endswith("ʔ")
        and body[-1:] in _VOWEL_LETTERS
        and body[:-1] == stem_plain[:-1]
    ):
        return f"]n]{stem_plain[:-1]}(ʔ{hom}[&{body[-1]}"
    if body.startswith(stem_plain):
        return f"]n]{stem_plain}{hom}[{body[len(stem_plain):]}"
    return None


def analysis_for_entry(
    surface: str,
    e: Entry,
    morph_values: Optional[Sequence[str]] = None,
    allow_prefix_restoration: bool = False,
) -> str:
    s = normalize_analysis(surface)
    hom = f"({e.hom})" if e.hom else ""
    stem_marker = stem_marker_from_morph(morph_values or [])

    if is_verb_pos(e.pos):
        stem = lemma_to_letters(e.lemma, fallback=s)
        if stem_marker == "]t]" and stem:
            # Xt stems place the t infix after the first root radical.
            stem = stem[0] + "]t]" + stem[1:]
            stem_marker = ""
        stem = maybe_expand_l_stem_terminal_gemination(
            stem=stem,
            surface_plain=extract_letters(s),
            stem_marker=stem_marker,
            morph_values=morph_values or [],
        )
        stem_plain = extract_letters(stem)
        stem_marker_plain = extract_letters(stem_marker)
        surface_plain = extract_letters(s)
        if is_iii_aleph_root(e.lemma) and has_prefix_morphology(morph_values or []):
            contracted_analysis = build_prefixed_iii_aleph_analysis(
                surface_plain=surface_plain,
                stem=stem,
                hom=hom,
                stem_marker=stem_marker,
                restore_initial_n=is_n_weak_iii_aleph_root(e.lemma),
            )
            if contracted_analysis is not None:
                return contracted_analysis
        if is_n_weak_iii_aleph_root(e.lemma) and has_prefix_morphology(morph_values or []):
            contracted_analysis = build_prefixed_n_weak_iii_aleph_analysis(
                surface_plain=surface_plain,
                stem=stem,
                hom=hom,
                stem_marker=stem_marker,
            )
            if contracted_analysis is not None:
                return contracted_analysis
        prefix_match = prefixed_verb_match(
            surface_plain=surface_plain,
            stem_plain=stem_plain,
            stem_marker_plain=stem_marker_plain,
        )
        if prefix_match is not None:
            prefix_tail, hidden_stem_letters = prefix_match
            stem_out = stem
            if hidden_stem_letters > 0:
                stem_out = mark_hidden_terminal_stem_letters(stem_out, hidden_stem_letters)
            marker = format_preformative_marker(surface_plain[0])
            return f"{marker}{stem_marker}{stem_out}{hom}[{prefix_tail}"
        if (
            allow_prefix_restoration
            and not stem_marker
            and stem_plain
            and surface_plain
            and surface_plain.startswith("š")
            and len(surface_plain) == len(stem_plain) + 1
            and surface_plain[1:] == stem_plain
        ):
            # Redirect-derived forms can surface with initial š while the
            # referenced lexeme is bare (e.g. /b-ʕ-r/ -> šbʕr). Encode as Š-prefix
            # restoration instead of a spurious trailing suffix fragment.
            return f"]š]{stem}{hom}["
        if (
            allow_prefix_restoration
            and stem_plain
            and surface_plain
            and len(stem_plain) == len(surface_plain)
            and stem_plain[0] == "y"
            and surface_plain[0] == "w"
            and stem_plain[1:] == surface_plain[1:]
        ):
            # Redirect target can be a weak-initial y-root while surface keeps w.
            return f"{stem_marker}(y&{surface_plain}{hom}["
        if has_prefix_morphology(morph_values or []):
            prefixed_fallback = build_prefixed_weak_fallback_analysis(
                surface_plain=surface_plain,
                stem_plain=stem_plain,
                stem_marker=stem_marker,
                hom=hom,
            )
            if prefixed_fallback is not None:
                return prefixed_fallback
        assimilated = build_s_stem_assimilation_analysis(
            surface_plain=surface_plain,
            stem=stem,
            stem_plain=stem_plain,
            stem_marker_plain=stem_marker_plain,
            hom=hom,
        )
        if assimilated is not None:
            return assimilated
        if has_n_suffix_morphology(morph_values or []):
            n_suffix = build_n_suffix_analysis(
                surface_plain=surface_plain,
                stem_plain=stem_plain,
                hom=hom,
            )
            if n_suffix is not None:
                return n_suffix
        realized = build_aleph_realization_analysis(
            surface_plain=surface_plain,
            stem_plain=stem_plain,
            stem_marker=stem_marker,
            hom=hom,
        )
        if realized is not None:
            return realized
        hidden_initial = build_hidden_initial_radical_analysis(
            surface_plain=surface_plain,
            stem_plain=stem_plain,
            stem_marker=stem_marker,
            hom=hom,
        )
        if hidden_initial is not None:
            return hidden_initial
        # A tail after '[' is only sound when the surface actually starts
        # with the (marker+)stem letters; fabricating one from unmatched
        # trailing surface letters created analyses that were wrong by
        # construction (ṯṯb -> ]š]ṯb[b, tṯṯb -> ]š]ṯb[ṯb).
        tail = ""
        marker_plus_stem = f"{stem_marker_plain}{stem_plain}"
        if marker_plus_stem and surface_plain.startswith(marker_plus_stem):
            tail = surface_plain[len(marker_plus_stem) :]
        elif stem_plain and surface_plain.startswith(stem_plain):
            tail = surface_plain[len(stem_plain) :]
        # Aleph is reconstructed rather than a written alphabetic sign in
        # the analysis notation, including unmatched fallback forms.
        stem = re.sub(r"(?<!\()ʔ", "(ʔ", stem)
        return f"{stem_marker}{stem}{hom}[{tail}"

    lex = lemma_to_letters(e.lemma, fallback=s)
    if (
        "/" in (e.lemma or "")
        and not ((e.lemma or "").startswith("/") and (e.lemma or "").endswith("/"))
        and len(lex) <= 2
        and len(s) >= 2
    ):
        # Slash-variant lemmas like ỉ/ủšḫry can collapse to a one-letter
        # fragment if we keep only the first variant. Prefer the observed
        # token shape in these short-fragment cases.
        lex = s
    if allow_prefix_restoration and is_nominal_pos(e.pos):
        lex_plain = extract_letters(lex)
        surface_plain = extract_letters(s)
        if (
            lex_plain
            and surface_plain
            and len(lex_plain) > len(surface_plain)
            and lex_plain.endswith(surface_plain)
        ):
            prefix_len = len(lex_plain) - len(surface_plain)
            if prefix_len <= 3:
                lex = mark_reconstructed_prefix_letters(lex, prefix_len)
    if takes_nominal_slash(e.pos):
        lex_plain = extract_letters(lex)
        surface_plain = extract_letters(s)
        if (
            lex_plain
            and surface_plain
            and lex_plain.endswith(("y", "w"))
            and surface_plain == f"{lex_plain[:-1]}n"
        ):
            return f"{lex[:-1]}({lex[-1]}{hom}/n"
        if lex_plain and surface_plain and lex_plain != surface_plain:
            if surface_plain.startswith(lex_plain):
                ending = surface_plain[len(lex_plain) :]
                if ending and set(ending) <= {"m", "t"}:
                    # Plural/feminine ending material goes after the closure
                    # (limm -> lim/m, rpum -> rpu/m).
                    return f"{lex}{hom}/{ending}"
            aligned = build_aligned_nominal_analysis(
                surface_plain=surface_plain,
                lex_plain=lex_plain,
                hom=hom,
            )
            if aligned is not None:
                return aligned
        return f"{lex}{hom}/"
    lex_plain = extract_letters(lex)
    surface_plain = extract_letters(s)
    if lex_plain != surface_plain:
        if lex_plain and surface_plain.startswith(lex_plain):
            tail = surface_plain[len(lex_plain) :]
            if tail:
                return f"{lex}{hom}&{tail}"
        return f"{s}{hom}"
    return f"{lex}{hom}"


def suffix_fragment(e: Entry) -> str:
    frag = lemma_to_letters(e.lemma.lstrip("-"), fallback=e.lemma.lstrip("-"))
    if e.hom:
        return f"{frag}({e.hom})"
    return frag


def inject_surface_only_tail_before_nominal_closure(analysis: str, base_surface: str) -> str:
    """Preserve visible non-lexeme tail letters in nominal split heads.

    Example:
    - base surface `qdqdh`, nominal head `qdqd/` -> `qdqd&h/`
    """
    value = (analysis or "").strip()
    if not value:
        return value
    match = _BASE_NOMINAL_ANALYSIS_RE.match(value)
    if match is None:
        return value

    lemma = match.group("lemma") or ""
    hom = match.group("hom") or ""
    lex_plain = extract_letters(lemma)
    surface_plain = extract_letters(normalize_analysis(base_surface))
    if not lex_plain or not surface_plain:
        return value
    if not surface_plain.startswith(lex_plain):
        return value
    if len(surface_plain) <= len(lex_plain):
        return value

    tail = surface_plain[len(lex_plain) :]
    if not tail:
        return value
    return f"{lemma}{hom}&{tail}/"


def inferred_stem_from_analysis(analysis: str) -> str:
    value = (analysis or "").strip()
    if not value:
        return ""
    if ":pass" in value:
        if "]š]" in value:
            return "Špass."
        if ":d" in value:
            return "Dpass."
        return "Gpass."
    if ":d" in value:
        return "D"
    if ":l" in value:
        return "L"
    if ":r" in value:
        return "R"
    if "]š]" in value:
        return "Š"
    if "]n]" in value:
        return "N"
    if "]t]" in value:
        return "Gt"
    return "G"


def inferred_stem_from_morph_values(morph_values: Sequence[str]) -> str:
    merged = " | ".join(morph_values or [])
    if not merged:
        return ""
    if "Špass." in merged:
        return "Špass."
    if "Dpass." in merged:
        return "Dpass."
    if "Gpass." in merged:
        return "Gpass."
    if re.search(r"\bŠt\b", merged):
        return "Št"
    if re.search(r"\bGt\b", merged):
        return "Gt"
    if re.search(r"\bDt\b", merged):
        return "Dt"
    if re.search(r"\bLt\b", merged):
        return "Lt"
    if re.search(r"\bRt\b", merged):
        return "Rt"
    if re.search(r"\bŠ\b", merged):
        return "Š"
    if re.search(r"\bD\b", merged):
        return "D"
    if re.search(r"\bL\b", merged):
        return "L"
    if re.search(r"\bR\b", merged):
        return "R"
    if re.search(r"\bN\b", merged):
        return "N"
    if re.search(r"\bG\b", merged):
        return "G"
    return ""


def gloss_for_entry(
    e: Entry,
    analysis: str = "",
    multi_slot: bool = False,
    section_ref: str = "",
    translation_index: DulatAttestationTranslationIndex | None = None,
    stem_name: str = "",
) -> str:
    if (e.pos or "").strip() == "→":
        return "?"
    pos_up = e.pos or ""
    if any(tag in pos_up for tag in ("DN", "PN", "TN", "GN")):
        # Prefer canonical name rendering for proper names if available.
        base = compact_gloss(e.wiki_tr) or compact_gloss(e.gloss) or entry_label(e)
    else:
        base = ""
        preferred_stem = stem_name or inferred_stem_from_analysis(analysis)
        if section_ref and translation_index is not None:
            reference_glosses = translation_index.sense_definitions_for_entry(
                e.entry_id,
                section_ref,
                stem_name=preferred_stem if is_verb_pos(pos_up) else "",
            )
            if reference_glosses:
                base = normalize_reference_sense_gloss(reference_glosses[0])
        if is_verb_pos(pos_up) and analysis and e.stem_glosses and not base:
            base = compact_gloss(
                e.stem_glosses.get(preferred_stem)
                or (
                    e.stem_glosses.get("D")
                    if preferred_stem in {"Dpass.", "Dt", "tD"}
                    else e.stem_glosses.get("G")
                )
                or ""
            )
        if not base:
            base = compact_gloss(e.gloss)
    if not base:
        base = ""
    if multi_slot:
        base = base.replace(",", " / ")
    return base


# ------------------ loading ------------------


def load_entries(
    dulat_db: Path,
    entry_patches: Optional[Dict[int, Dict[str, str]]] = None,
) -> Tuple[
    Dict[int, Entry],
    Dict[str, List[Entry]],
    Dict[str, List[Entry]],
    Dict[str, List[Entry]],
    Dict[Tuple[str, int], Set[str]],
]:
    if entry_patches is None:
        entry_patches = load_dulat_entry_patches(
            Path(__file__).resolve().parents[1] / "data_sources" / "dulat_entry_patches.tsv"
        )
    conn = sqlite3.connect(str(dulat_db))
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(entries)")
    entry_columns = {row[1] for row in cur.fetchall()}
    has_summary = "summary" in entry_columns
    has_text = "text" in entry_columns

    # compact gloss preference
    sense_map: Dict[int, str] = {}
    cur.execute(
        "SELECT entry_id, definition "
        "FROM senses "
        "WHERE definition IS NOT NULL AND trim(definition) != '' "
        "ORDER BY entry_id, id"
    )
    for entry_id, definition in cur.fetchall():
        if entry_id in sense_map:
            continue
        if not is_usable_sense_definition(definition or ""):
            continue
        compact = compact_gloss(definition)
        if compact:
            sense_map[entry_id] = compact

    stem_gloss_map: Dict[int, Dict[str, str]] = defaultdict(dict)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stems' LIMIT 1")
    has_stems = cur.fetchone() is not None
    if has_stems:
        cur.execute(
            "SELECT stems.entry_id, stems.name, senses.definition, stems.gloss "
            "FROM stems "
            "LEFT JOIN senses ON senses.stem_id = stems.id "
            "ORDER BY stems.entry_id, stems.id, senses.id"
        )
        for entry_id, stem_name, definition, stem_gloss in cur.fetchall():
            if not stem_name or stem_name in stem_gloss_map.get(entry_id, {}):
                continue
            compact = ""
            if is_usable_sense_definition(definition or ""):
                compact = compact_gloss(definition)
            if not compact:
                compact = compact_gloss(stem_gloss or "")
            if compact:
                stem_gloss_map[int(entry_id)][stem_name] = compact

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

    summary_expr = "summary" if has_summary else "'' AS summary"
    text_expr = "text" if has_text else "'' AS text"
    cur.execute(
        "SELECT entry_id, lemma, homonym, pos, wiki_transcription, "
        f"{summary_expr}, {text_expr} "
        "FROM entries"
    )
    entries_by_id: Dict[int, Entry] = {}
    lemma_map: Dict[str, List[Entry]] = {}
    suffix_map: Dict[str, List[Entry]] = {}
    entry_text_by_id: Dict[int, str] = {}
    for entry_id, lemma, hom, pos, wiki_tr, summary, text in cur.fetchall():
        patch = entry_patches.get(int(entry_id), {})
        lemma = patch.get("lemma", lemma)
        hom = patch.get("homonym", hom)
        pos = patch.get("pos", pos)
        lm, hm = parse_optional_hom(lemma or "", hom or "")
        redirect_targets = ()
        if (pos or "").strip() == "→":
            redirect_targets = extract_redirect_targets(summary or "", text or "")
        e = Entry(
            entry_id=int(entry_id),
            lemma=lm,
            hom=hm,
            pos=pos or "",
            gloss=trans_map.get(entry_id) or sense_map.get(entry_id, ""),
            wiki_tr=wiki_tr or "",
            stem_glosses=stem_gloss_map.get(int(entry_id), {}),
            redirect_targets=redirect_targets,
        )
        if text:
            entry_text_by_id[e.entry_id] = text
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
    seen_form_entry: Set[Tuple[str, int]] = set()
    cur.execute("SELECT text, entry_id FROM forms WHERE text IS NOT NULL AND trim(text) != ''")
    for txt, entry_id in cur.fetchall():
        e = entries_by_id.get(int(entry_id))
        if not e:
            continue
        for form_variant in expand_dulat_form_texts(
            lemma=e.lemma,
            homonym=e.hom,
            form_text=txt or "",
        ):
            k = normalize_lookup(form_variant)
            if k:
                marker = (k, e.entry_id)
                if marker in seen_form_entry:
                    continue
                seen_form_entry.add(marker)
                forms_map.setdefault(k, []).append(e)
    cur.execute(
        "SELECT text, entry_id, morphology FROM forms WHERE text IS NOT NULL AND trim(text) != ''"
    )
    for txt, entry_id, morph in cur.fetchall():
        e = entries_by_id.get(int(entry_id))
        if not e:
            continue
        morph_value = override_dulat_form_morphology(
            lemma=e.lemma,
            homonym=e.hom,
            form_text=txt or "",
            morphology=(morph or "").strip(),
        )
        for form_variant in expand_dulat_form_texts(
            lemma=e.lemma,
            homonym=e.hom,
            form_text=txt or "",
        ):
            k = normalize_lookup(form_variant)
            if not k:
                continue
            forms_morph.setdefault((k, int(entry_id)), set()).add(morph_value)

    for entry_id, entry_text in entry_text_by_id.items():
        e = entries_by_id.get(entry_id)
        if e is None:
            continue
        for fallback_form in extract_forms_from_entry_text(entry_text):
            for form_variant in expand_dulat_form_texts(
                lemma=e.lemma,
                homonym=e.hom,
                form_text=fallback_form,
            ):
                k = normalize_lookup(form_variant)
                if not k:
                    continue
                marker = (k, e.entry_id)
                if marker in seen_form_entry:
                    continue
                seen_form_entry.add(marker)
                forms_map.setdefault(k, []).append(e)

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
        form_morph_values = set(forms_morph.get((normalize_lookup(surface), pe.entry_id), set()))
        if len(v.entries) == 1 and normalize_lookup(v.base_surface) != normalize_lookup(surface):
            form_morph_values.update(
                forms_morph.get((normalize_lookup(v.base_surface), pe.entry_id), set())
            )
        fm = " | ".join(sorted(form_morph_values)).lower()
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


def dedupe_suffix_entries(entries: Iterable[Entry]) -> List[Entry]:
    """Deduplicate suffix entries by surface segment (ignore homonym numerals).

    For split-variant ranking we only need one representative per suffix segment
    (e.g. `-y (I)` vs `-y (II)`); downstream normalization already strips
    homonym numerals from suffix markers.
    """
    seen: set[str] = set()
    out: list[Entry] = []
    for e in entries:
        key = normalize_lookup((e.lemma or "").lstrip("-"))
        if not key:
            key = normalize_lookup(e.lemma or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _variant_has_exact_lexical_head(variant: Variant, surface: str) -> bool:
    """Return whether a one-entry candidate is an exact lexical headword hit.

    Exact homonyms receive a slightly wider viability window than derived or
    reconstructed hypotheses. Contextual stages may still disambiguate them
    from direct attestations, formulas, or local syntax later in the pipeline.
    """
    if len(variant.entries) != 1:
        return False
    entry = variant.entries[0]
    if (entry.lemma or "").startswith("-"):
        return False
    lemma = normalize_lookup(entry.lemma)
    return lemma in {normalize_lookup(surface), normalize_lookup(variant.base_surface)}


def _variant_has_redirect_evidence(variant: Variant) -> bool:
    if variant.from_redirect:
        return True
    return any((entry.pos or "").strip() == "→" for entry in variant.entries)


def select_viable_ranked_variants(
    variants: Sequence[Variant],
    *,
    surface: str,
    max_variants: int,
) -> List[Variant]:
    """Select a compact candidate bundle without frequency-only collapse.

    Scores remain useful for ranking and for discarding weak reconstructions,
    but exact lexical homonyms are protected inside the hard review ceiling.
    This leaves genuine disambiguation to evidence-bearing downstream stages.
    """
    if not variants or max_variants <= 0:
        return []

    best_score = variants[0].score
    viable: List[Variant] = []
    for variant in variants:
        if len(variant.entries) > 1:
            score_window = VIABLE_SPLIT_SCORE_WINDOW
        elif _variant_has_exact_lexical_head(variant, surface):
            score_window = VIABLE_EXACT_SCORE_WINDOW
        else:
            score_window = VIABLE_DERIVED_SCORE_WINDOW
        if (
            _variant_has_redirect_evidence(variant)
            or (best_score - variant.score) <= score_window
        ):
            viable.append(variant)
    return viable[:max_variants]


def is_function_word_like(entry: Entry) -> bool:
    """Return True for short function-word entries that should not outrank exact lexemes."""
    pos = (entry.pos or "").lower()
    if (entry.lemma or "").startswith("-"):
        return True
    return any(token in pos for token in ("functor", "adv.", "prep.", "conj.", "det."))


def is_proper_name_pos(pos: str) -> bool:
    """Return True for PN onomastic candidates, but not personal pronouns."""
    raw = (pos or "").strip()
    return "pers. pn." not in raw.lower() and bool(re.search(r"\bPN\b", raw))


def variant_is_proper_name(variant: Variant) -> bool:
    lexical_entries = [
        entry for entry in variant.entries if not (entry.lemma or "").startswith("-")
    ]
    return any(is_proper_name_pos(entry.pos) for entry in lexical_entries)


def variant_has_non_pn_lexical_reading(variant: Variant) -> bool:
    lexical_entries = [
        entry for entry in variant.entries if not (entry.lemma or "").startswith("-")
    ]
    if not lexical_entries:
        return False
    if all((entry.pos or "").strip() == "→" for entry in lexical_entries):
        return False
    return not variant_is_proper_name(variant)


def variant_has_direct_dulat_attestation(
    variant: Variant,
    current_ref: str,
    direct_reference_index: DulatAttestationIndex | None,
) -> bool:
    if direct_reference_index is None or not current_ref:
        return False
    for entry in variant.entries:
        if not is_proper_name_pos(entry.pos):
            continue
        if direct_reference_index.has_reference_for_variant_token(entry_label(entry), current_ref):
            return True
    return False


def prune_unattested_pn_variants(
    variants: List[Variant],
    current_ref: str,
    direct_reference_index: DulatAttestationIndex | None,
) -> List[Variant]:
    """Keep PN variants only when directly attested for this line or alone."""
    pn_variants = [variant for variant in variants if variant_is_proper_name(variant)]
    other_variants = [
        variant for variant in variants if variant_has_non_pn_lexical_reading(variant)
    ]
    if not pn_variants or not other_variants:
        return variants

    kept_pn_variants = [
        variant
        for variant in pn_variants
        if variant_has_direct_dulat_attestation(
            variant=variant,
            current_ref=current_ref,
            direct_reference_index=direct_reference_index,
        )
    ]
    return other_variants + kept_pn_variants


def build_variants(
    surface: str,
    current_ref: str,
    forms_map: Dict[str, List[Entry]],
    lemma_map: Dict[str, List[Entry]],
    suffix_map: Dict[str, List[Entry]],
    forms_morph: Dict[Tuple[str, int], Set[str]],
    mention_ids: Set[int],
    entry_ref_count: Dict[int, int],
    entry_tablets: Dict[int, Set[str]],
    entry_family_count: Dict[int, Dict[str, int]],
    direct_reference_index: DulatAttestationIndex | None = None,
    max_variants: int = 3,
    editorial_lookup_surface: str = "",
) -> List[Variant]:
    s_norm = normalize_lookup(surface)
    lookup_surfaces = [surface]
    editorial_norm = normalize_lookup(editorial_lookup_surface)
    if editorial_norm and editorial_norm != s_norm:
        lookup_surfaces.append(editorial_lookup_surface)

    direct_source_by_id: Dict[int, str] = {}
    direct_candidates: List[Entry] = []
    editorial_direct_ids: Set[int] = set()
    for lookup_surface in lookup_surfaces:
        lookup_norm = normalize_lookup(lookup_surface)
        lookup_entries = list(forms_map.get(lookup_norm, []))
        if lookup_norm == editorial_norm and lookup_norm != s_norm:
            # A corrected editorial reading is lexical evidence, not merely an
            # inflected-form hit. Include exact lemma homonyms that the forms
            # index can omit when another homonym owns the explicit form row.
            lookup_entries.extend(lemma_map.get(lookup_norm, []))
        for entry in dedupe_entries(lookup_entries):
            if entry.entry_id not in direct_source_by_id:
                direct_source_by_id[entry.entry_id] = lookup_surface
                direct_candidates.append(entry)
            if lookup_norm == editorial_norm and lookup_norm != s_norm:
                editorial_direct_ids.add(entry.entry_id)

    direct_all = dedupe_entries(direct_candidates)
    direct_pref = [e for e in direct_all if (e.pos or "").strip() and (e.pos or "").strip() != "→"]
    direct = direct_pref if direct_pref else direct_all
    lookup_norms = {normalize_lookup(value) for value in lookup_surfaces}
    direct_has_exact_form = any(
        (lookup_norm, entry.entry_id) in forms_morph
        for lookup_norm in lookup_norms
        for entry in direct
    )
    direct_exact_lexical = [
        e
        for e in direct
        if not (e.lemma or "").startswith("-")
        and (e.pos or "").strip()
        and (e.pos or "").strip() != "→"
        and normalize_lookup(e.lemma) in lookup_norms
    ]
    direct_exact_lexical_ids = {e.entry_id for e in direct_exact_lexical}
    direct_ids = {e.entry_id for e in direct}

    variants: List[Variant] = [
        Variant((entry,), direct_source_by_id.get(entry.entry_id, surface)) for entry in direct
    ]

    # Expand lexical variants from redirect-only entries (pos = "→") using
    # explicit cf.-targets from DULAT entry notes.
    for redirect_entry in [e for e in direct if (e.pos or "").strip() == "→"]:
        for target in redirect_entry.redirect_targets:
            target_lemma, target_hom = parse_optional_hom(target, "")
            target_key = normalize_lookup(target_lemma)
            if not target_key:
                continue
            target_is_slash_root = target_lemma.startswith("/") and target_lemma.endswith("/")
            target_entries = dedupe_entries(lemma_map.get(target_key, []))
            filtered_targets = [
                entry
                for entry in target_entries
                if entry.entry_id != redirect_entry.entry_id
                and (entry.pos or "").strip()
                and (entry.pos or "").strip() != "→"
                and (not target_hom or (entry.hom or "") == target_hom)
                and (
                    not target_is_slash_root
                    or (entry.lemma.startswith("/") and entry.lemma.endswith("/"))
                )
            ]
            for target_entry in filtered_targets[:2]:
                variants.append(
                    Variant(
                        (target_entry,),
                        direct_source_by_id.get(redirect_entry.entry_id, surface),
                        from_redirect=True,
                    )
                )

    # Conservative suffix splitting:
    # - when direct form mapping failed, or
    # - when direct candidates come only from lemma fallback (no exact form hit).
    if ((not direct) or (direct and not direct_has_exact_form)) and not editorial_direct_ids:
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
            if direct_exact_lexical_ids:
                base_entries = [
                    e for e in base_entries if e.entry_id not in direct_exact_lexical_ids
                ]
                if not base_entries:
                    continue
                base_has_exact_form = any(
                    (base_norm, e.entry_id) in forms_morph for e in base_entries
                )
                if not base_has_exact_form:
                    continue
                if all(is_function_word_like(e) for e in base_entries):
                    continue
            if not base_entries:
                continue
            suffix_all = dedupe_entries(suffix_map.get(suf, []))
            suffix_pref = [
                e for e in suffix_all if (e.pos or "").strip() and (e.pos or "").strip() != "→"
            ]
            suffix_entries = suffix_pref if suffix_pref else suffix_all
            suffix_entries = dedupe_suffix_entries(suffix_entries)
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
    variants = prune_unattested_pn_variants(
        variants=variants,
        current_ref=current_ref,
        direct_reference_index=direct_reference_index,
    )

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
    # Exact-line reverse mentions are strong ranking evidence, but they are not
    # an exhaustive annotation of every viable reading.  In particular, a
    # dictionary citation may discuss only one of several homonyms on the line.
    # Keep the score boost above and leave elimination to the viability window
    # plus evidence-bearing contextual stages.
    has_redirect_pair = any(v.from_redirect for v in variants) and any(
        len(v.entries) == 1 and (v.entries[0].pos or "").strip() == "→" for v in variants
    )
    top = select_viable_ranked_variants(
        variants,
        surface=surface,
        max_variants=max_variants,
    )
    if has_redirect_pair and not any(
        len(v.entries) == 1 and (v.entries[0].pos or "").strip() == "→" for v in top
    ):
        arrow_variant = next(
            (
                v
                for v in variants
                if len(v.entries) == 1 and (v.entries[0].pos or "").strip() == "→"
            ),
            None,
        )
        if arrow_variant is not None:
            if len(top) >= max_variants:
                top = top[:-1]
            top.append(arrow_variant)
    return top


def render_variant(
    surface: str,
    v: Variant,
    forms_morph: Dict[Tuple[str, int], Set[str]],
    section_ref: str = "",
    translation_index: DulatAttestationTranslationIndex | None = None,
) -> Tuple[str, str, str, str]:
    entries = list(v.entries)
    if len(entries) == 1:
        e = entries[0]
        morph_values = set(forms_morph.get((normalize_lookup(surface), e.entry_id), set()))
        morph_values.update(
            forms_morph.get((normalize_lookup(v.base_surface), e.entry_id), set())
        )
        mv = sorted(morph_values)
        a = analysis_for_entry(
            surface,
            e,
            morph_values=mv,
            allow_prefix_restoration=bool(v.from_redirect),
        )
        d = entry_label(e)
        p = pos_token(e)
        stem_name = inferred_stem_from_morph_values(mv) or inferred_stem_from_analysis(a)
        g = gloss_for_entry(
            e,
            analysis=a,
            multi_slot=False,
            section_ref=section_ref,
            translation_index=translation_index,
            stem_name=stem_name,
        )
        return a, d, p, g

    base, suf = entries[0], entries[1]
    mv = sorted(forms_morph.get((normalize_lookup(v.base_surface), base.entry_id), set()))
    base_analysis = analysis_for_entry(v.base_surface, base, morph_values=mv)
    base_analysis = inject_surface_only_tail_before_nominal_closure(
        analysis=base_analysis,
        base_surface=v.base_surface,
    )
    a = f"{base_analysis}+{suffix_fragment(suf)}"
    d = f"{entry_label(base)},{entry_label(suf)}"
    p = f"{pos_token(base)},{pos_token(suf)}"
    base_stem_name = inferred_stem_from_morph_values(mv) or inferred_stem_from_analysis(
        base_analysis
    )
    base_gloss = gloss_for_entry(
        base,
        analysis=base_analysis,
        multi_slot=True,
        section_ref=section_ref,
        translation_index=translation_index,
        stem_name=base_stem_name,
    )
    g = f"{base_gloss},{gloss_for_entry(suf, multi_slot=True)}"
    return a, d, p, g


def refine_file(
    path: Path,
    out_path: Path,
    forms_map: Dict[str, List[Entry]],
    lemma_map: Dict[str, List[Entry]],
    suffix_map: Dict[str, List[Entry]],
    forms_morph: Dict[Tuple[str, int], Set[str]],
    reverse_mentions: Dict[str, Set[int]],
    entry_ref_count: Dict[int, int],
    entry_tablets: Dict[int, Set[str]],
    entry_family_count: Dict[int, Dict[str, int]],
    direct_reference_index: DulatAttestationIndex | None = None,
    translation_index: DulatAttestationTranslationIndex | None = None,
    only_not_found: bool = False,
    editorial_lookup_overrides: Optional[Dict[str, str]] = None,
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
        editorial_lookup_surface = (editorial_lookup_overrides or {}).get(line_id, "")

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

        # Exact-line mentions only: neighbour-line fallback proved unsafe for
        # ranking (it boosted a leaked /y-t-n/ row for surface gh at KTU 1.16
        # II:36 via the II:35 citation and pushed out the correct g+h row).
        mention_ids = (
            mentions_for_ref(reverse_mentions, current_ref, line_tolerance=0)
            if current_ref
            else set()
        )
        variants = build_variants(
            surface,
            current_ref,
            forms_map,
            lemma_map,
            suffix_map,
            forms_morph,
            mention_ids,
            entry_ref_count,
            entry_tablets,
            entry_family_count,
            direct_reference_index=direct_reference_index,
            max_variants=AUTOMATIC_MAX_VARIANTS,
            editorial_lookup_surface=editorial_lookup_surface,
        )

        if not variants:
            if only_not_found:
                out_lines.append(raw)
                rows += 1
                continue
            new_parts = [line_id, surface, surface, "", "", "", "DULAT: NOT FOUND"]
        else:
            rendered: List[Tuple[str, str, str, str]] = []
            for v in variants:
                rendered.append(
                    render_variant(
                        surface,
                        v,
                        forms_morph=forms_morph,
                        section_ref=current_ref,
                        translation_index=translation_index,
                    )
                )
            # No reconstructability gating here: rendering is deliberately
            # followed by repair steps (plural split, suffix clitics, weak
            # preformatives), so baselines like il(I)/ for ilm only become
            # reconstructable later. The end-of-pipeline fallback step turns
            # what still cannot reconstruct after repair into '?' + hint.
            used_editorial_lookup = bool(
                editorial_lookup_surface
                and any(
                    normalize_lookup(candidate.base_surface)
                    == normalize_lookup(editorial_lookup_surface)
                    for candidate in variants
                )
            )
            new_parts = [
                line_id,
                surface,
                ";".join(item[0] for item in rendered),
                ";".join(item[1] for item in rendered),
                ";".join(item[2] for item in rendered),
                ";".join(item[3] for item in rendered),
                f"KTU corrected: {editorial_lookup_surface}" if used_editorial_lookup else "",
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
    paths = get_project_paths(REPO_ROOT)
    ap = argparse.ArgumentParser(
        description="Refine morphology TSV using reverse mentions + clitic splitting"
    )
    ap.add_argument("files", nargs="+", help="TSV files to refine")
    ap.add_argument("--dulat-db", default=str(paths.default_dulat_db()))
    ap.add_argument("--udb-db", default=str(paths.default_udb_db()))
    ap.add_argument("--in-place", action="store_true", help="Rewrite files in place")
    ap.add_argument("--out-dir", default="results", help="Output dir if not --in-place")
    ap.add_argument(
        "--only-not-found",
        action="store_true",
        help="Refine only rows currently marked with DULAT: NOT FOUND",
    )
    args = ap.parse_args()

    _entries_by_id, forms_map, lemma_map, suffix_map, forms_morph = load_entries(
        Path(args.dulat_db)
    )
    reverse_mentions, entry_ref_count, entry_tablets, entry_family_count = load_reverse_mentions(
        Path(args.dulat_db), Path(args.udb_db)
    )
    direct_reference_index = DulatAttestationIndex.from_sqlite(Path(args.dulat_db))
    translation_index = DulatAttestationTranslationIndex.from_sqlite(Path(args.dulat_db))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in args.files:
        src = Path(f)
        dst = src if args.in_place else out_dir / src.name
        rows, changed = refine_file(
            src,
            dst,
            forms_map,
            lemma_map,
            suffix_map,
            forms_morph,
            reverse_mentions,
            entry_ref_count,
            entry_tablets,
            entry_family_count,
            direct_reference_index=direct_reference_index,
            translation_index=translation_index,
            only_not_found=args.only_not_found,
        )
        print(f"{src} -> {dst} | rows={rows} changed={changed}")


if __name__ == "__main__":
    main()
