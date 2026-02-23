#!/usr/bin/env python3
"""
Extract conservative morphology evidence from notarius.compact.html.

This script targets line-linked analytical claims (participles, stem labels,
ambiguity notes) rather than full-text parsing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from itertools import product


PARA_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
BOLD_RE = re.compile(r"<b[^>]*>(.*?)</b>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")

# CAT/KTU style references in prose and notes.
REF_RE = re.compile(
    r"\b\d+\.\d{1,3}(?:\s+[IVX]+)?\s+\d+(?:[-–]\d+)?\b"
    r"|\b\d+\.\d{1,3}:\d+(?:[-–]\d+)?\b"
)

KEYWORD_RULES = {
    "active_participle": re.compile(r"\bactive participle\b", re.IGNORECASE),
    "passive_participle": re.compile(r"\bpassive participle\b", re.IGNORECASE),
    "agent_noun": re.compile(r"\bagent noun\b|\bnomen agentis\b", re.IGNORECASE),
    "attributive": re.compile(r"\battributive\b", re.IGNORECASE),
    "substantivized": re.compile(r"\bsubstantivized\b", re.IGNORECASE),
    "circumstantial": re.compile(r"\bcircumstantial\b", re.IGNORECASE),
    "predicative": re.compile(r"\bpredicative\b", re.IGNORECASE),
    "infinitive": re.compile(r"\binfinitive\b", re.IGNORECASE),
    "suffix_conjugation": re.compile(r"\bsuffix-?conjugation\b|\bSC\b", re.IGNORECASE),
    "g_stem": re.compile(r"\bG-?stem\b", re.IGNORECASE),
    "d_stem": re.compile(r"\bD-?stem\b", re.IGNORECASE),
    "n_stem": re.compile(r"\bN-?stem\b", re.IGNORECASE),
    "g_passive": re.compile(r"\bG passive\b|\bGpass\b", re.IGNORECASE),
    "ambiguity": re.compile(r"\bambiguous\b|\bambiguity\b", re.IGNORECASE),
    "debated": re.compile(r"\bdebated\b|\bobscure\b|\buncertain\b", re.IGNORECASE),
}

JUDGMENT_RE = re.compile(
    r"\b(can be interpreted as|can be parsed as|is interpreted as|parsed as|"
    r"preferable|preferred|I parse|I suggest|seems to|likely|unlikely|debated|uncertain)\b",
    re.IGNORECASE,
)

# Explicit parsing-decision signals.
CLAIM_RE = re.compile(
    r"\b(parsed as|parse(?:d)? as|is parsed|is interpreted as|interpreted as|"
    r"can be parsed as|can be interpreted as|I parse|I suggest|"
    r"preferable|preferred|is preferable|rather than|seems to)\b",
    re.IGNORECASE,
)
STRONG_CLAIM_RE = re.compile(
    r"\b(I parse|I suggest|is parsed as|is interpreted as|"
    r"preferable|preferred|is preferable|rather than)\b",
    re.IGNORECASE,
)
ARROW_RE = re.compile(r"\b[^\s]{1,24}\s*→\s*[^\s]{1,24}\b")

# Broad transliteration alphabet in current files.
UG_CHAR_RE = re.compile(r"[a-zḫḥṭṣṯẓġḏʔˀˁʕủỉảšśḳˤ]")
ASCII_TOKEN_RE = re.compile(r"^[a-z]+$")
EN_STOPWORDS = {
    "forms",
    "form",
    "are",
    "was",
    "were",
    "this",
    "that",
    "with",
    "from",
    "for",
    "into",
    "over",
    "under",
    "part",
    "total",
    "oetry",
    "plated",
    "blessed",
    "example",
}


def strip_tags(text: str) -> str:
    # Remove tags without injecting separators so split graphemes wrapped in
    # adjacent tags (e.g., <i>ḫ</i><i>t</i><i>ủ</i>) stay contiguous.
    return TAG_RE.sub("", text)


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\u00a0", " ")
    text = text.replace("–", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_ref(ref: str) -> str:
    ref = normalize_text(ref)
    ref = re.sub(r"\s+", " ", ref)
    return ref


def clean_token(token: str) -> str:
    token = html.unescape(token)
    token = token.replace("\u00a0", "")
    token = token.strip()
    token = token.strip("[](){}<>.,;:!?\"'“”‘’/")
    token = re.sub(r"\s+", "", token)
    token = token.replace("–", "-")
    return token


def expand_slash_alternatives(token: str) -> List[str]:
    """
    Expand slash-alternative segments inside a hyphenated form/root.
    Example:
      m-ḥ-w/y -> [m-ḥ-w, m-ḥ-y]
    """
    token = token.strip()
    if "/" not in token:
        return [token]

    # Operate only on hyphenated strings; otherwise keep token unchanged.
    if "-" not in token:
        return [token]

    segments = token.split("-")
    choices: List[List[str]] = []
    for seg in segments:
        seg = seg.strip()
        if not seg:
            return [token]
        if "/" in seg:
            opts = [s.strip() for s in seg.split("/") if s.strip()]
            if len(opts) < 2:
                return [token]
            choices.append(opts)
        else:
            choices.append([seg])

    expanded = ["-".join(parts) for parts in product(*choices)]
    # Stable unique
    return list(dict.fromkeys(expanded))


def is_ugaritic_token(token: str) -> bool:
    if not token or len(token) < 3 or len(token) > 32:
        return False
    if re.search(r"\d", token):
        return False
    if re.search(r"[A-Z]", token):
        return False
    if any(ch in token for ch in "[]<>"):
        return False
    if not UG_CHAR_RE.search(token):
        return False

    # Filter obvious English tokens when they are pure ASCII.
    if ASCII_TOKEN_RE.fullmatch(token):
        if token in EN_STOPWORDS:
            return False
        if any(ch in token for ch in "eov"):
            return False
        vowel_count = sum(ch in "aeiou" for ch in token)
        if len(token) >= 7 and vowel_count >= 3:
            return False
        if re.search(r"(ing|ed|tion|ions|ment|able|ness)$", token):
            return False
    return True


def extract_forms(paragraph_html: str) -> List[str]:
    forms: List[str] = []
    seen = set()

    # Merge adjacent formatting tags that belong to one graphemic form.
    merged_html = re.sub(r"</i><i[^>]*>", "", paragraph_html, flags=re.IGNORECASE)
    merged_html = re.sub(r"</b><b[^>]*>", "", merged_html, flags=re.IGNORECASE)

    # Keep extraction conservative: only bold chunks are used for forms.
    candidate_chunks = BOLD_RE.findall(merged_html)
    for chunk in candidate_chunks:
        chunk_text = normalize_text(strip_tags(chunk))
        # Keep '/' inside tokens so alternative radicals can be expanded later.
        for part in re.split(r"[,\s;]+", chunk_text):
            tok = clean_token(part)
            for variant in expand_slash_alternatives(tok):
                if not is_ugaritic_token(variant):
                    continue
                if variant in seen:
                    continue
                seen.add(variant)
                forms.append(variant)
    return forms


def detect_tags(text: str) -> List[str]:
    tags: List[str] = []
    for tag, rule in KEYWORD_RULES.items():
        if rule.search(text):
            tags.append(tag)
    return tags


def split_sentences(text: str) -> List[str]:
    # Conservative split; this is enough for excerpting claims.
    parts = re.split(r"(?<=[\.;!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def extract_claim_snippets(text: str, max_items: int = 4) -> List[str]:
    snippets: List[str] = []
    for sent in split_sentences(text):
        if JUDGMENT_RE.search(sent) or any(rule.search(sent) for rule in KEYWORD_RULES.values()):
            snippets.append(sent[:320])
        if len(snippets) >= max_items:
            break
    return snippets


def extract_parse_claim_snippets(text: str, max_items: int = 4) -> List[str]:
    snippets: List[str] = []
    for sent in split_sentences(text):
        if CLAIM_RE.search(sent) or ARROW_RE.search(sent):
            snippets.append(sent[:320])
        if len(snippets) >= max_items:
            break
    return snippets


def is_section_heading(text: str) -> bool:
    lower = text.lower()
    if text.startswith("Example "):
        return False
    if len(text) > 180:
        return False
    if re.match(r"^\d+(?:\.\d+){0,2}\s", text):
        return True
    if lower.startswith(("chapter ", "part ", "introduction", "conclusion", "summary:")):
        return True
    if "participle" in lower and len(text) < 120:
        return True
    return False


def detect_example(text: str) -> str:
    m = re.match(r"^Example\s+(\d+)\b", text, flags=re.IGNORECASE)
    return m.group(1) if m else ""


def score_entry(forms: List[str], tags: List[str], snippets: List[str], refs: List[str]) -> int:
    score = 0
    if refs:
        score += 1
    if forms:
        score += 1
    if len(tags) >= 2:
        score += 1
    elif tags:
        score += 0
    if snippets:
        score += 1
    if len(forms) >= 2:
        score += 1
    return score


def confidence_from_score(score: int) -> str:
    if score >= 5:
        return "high"
    if score == 4:
        return "medium"
    return "low"


def classify_entry(
    text: str,
    forms: List[str],
    tags: List[str],
    parse_claim_snippets: List[str],
) -> Tuple[str, str]:
    """
    Return (entry_type, claim_strength):
      - explicit_parse_claim | discussion_context
      - strong | moderate | weak | none
    """
    has_claim = bool(parse_claim_snippets)
    has_parse_tags = any(
        t in tags
        for t in (
            "active_participle",
            "passive_participle",
            "suffix_conjugation",
            "infinitive",
            "g_stem",
            "d_stem",
            "n_stem",
            "g_passive",
        )
    )
    has_strong_signal = STRONG_CLAIM_RE.search(text) is not None

    if has_claim and (forms or has_parse_tags):
        entry_type = "explicit_parse_claim"
        if has_strong_signal:
            claim_strength = "strong"
        else:
            claim_strength = "moderate"
    else:
        entry_type = "discussion_context"
        if has_claim:
            claim_strength = "weak"
        else:
            claim_strength = "none"
    return entry_type, claim_strength


def extract_evidence(html_text: str, min_score: int) -> Dict[str, object]:
    entries: List[Dict[str, object]] = []
    paragraphs = list(PARA_RE.finditer(html_text))

    current_section = ""
    current_example = ""

    for idx, match in enumerate(paragraphs, start=1):
        p_html = match.group(1)
        p_text = normalize_text(strip_tags(p_html))
        if not p_text:
            continue

        maybe_example = detect_example(p_text)
        if maybe_example:
            current_example = maybe_example
            continue
        if is_section_heading(p_text):
            current_section = p_text
            continue

        refs = [normalize_ref(r) for r in REF_RE.findall(p_text)]
        if not refs:
            continue
        refs = list(dict.fromkeys(refs))

        tags = detect_tags(p_text)
        forms = extract_forms(p_html)
        snippets = extract_claim_snippets(p_text)
        parse_claim_snippets = extract_parse_claim_snippets(p_text)
        entry_type, claim_strength = classify_entry(
            text=p_text,
            forms=forms,
            tags=tags,
            parse_claim_snippets=parse_claim_snippets,
        )

        score = score_entry(forms=forms, tags=tags, snippets=snippets, refs=refs)
        if score < min_score:
            continue

        entries.append(
            {
                "id": len(entries) + 1,
                "paragraph_index": idx,
                "source_offset": match.start(),
                "section": current_section,
                "example": current_example,
                "refs": refs,
                "forms": forms,
                "tags": tags,
                "snippets": snippets,
                "parse_claim_snippets": parse_claim_snippets,
                "entry_type": entry_type,
                "claim_strength": claim_strength,
                "confidence": confidence_from_score(score),
                "score": score,
                "text": p_text[:1200],
            }
        )

    refs_all = [ref for e in entries for ref in e["refs"]]
    stats = {
        "paragraphs_total": len(paragraphs),
        "entries_extracted": len(entries),
        "refs_total": len(refs_all),
        "refs_unique": len(set(refs_all)),
        "forms_total": sum(len(e["forms"]) for e in entries),
        "forms_unique": len({f for e in entries for f in e["forms"]}),
        "high_confidence": sum(1 for e in entries if e["confidence"] == "high"),
        "medium_confidence": sum(1 for e in entries if e["confidence"] == "medium"),
        "low_confidence": sum(1 for e in entries if e["confidence"] == "low"),
        "explicit_parse_claim": sum(1 for e in entries if e["entry_type"] == "explicit_parse_claim"),
        "discussion_context": sum(1 for e in entries if e["entry_type"] == "discussion_context"),
        "claim_strength_strong": sum(1 for e in entries if e["claim_strength"] == "strong"),
        "claim_strength_moderate": sum(1 for e in entries if e["claim_strength"] == "moderate"),
        "claim_strength_weak": sum(1 for e in entries if e["claim_strength"] == "weak"),
        "claim_strength_none": sum(1 for e in entries if e["claim_strength"] == "none"),
    }
    return {"entries": entries, "stats": stats}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract conservative morphology evidence from notarius HTML."
    )
    parser.add_argument(
        "--input",
        default="data/notarius.compact.html",
        help="Input notarius HTML file",
    )
    parser.add_argument(
        "--output",
        default="data/notarius_evidence.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=3,
        help="Minimum confidence score (default: 3)",
    )
    parser.add_argument(
        "--split-output",
        action="store_true",
        help="Also write sidecar files split by entry_type",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    html_text = input_path.read_text(encoding="utf-8")
    payload = extract_evidence(html_text, min_score=args.min_score)

    data = {
        "source": str(input_path),
        "created_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "min_score": args.min_score,
        "stats": payload["stats"],
        "entries": payload["entries"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.split_output:
        explicit = [e for e in payload["entries"] if e["entry_type"] == "explicit_parse_claim"]
        context = [e for e in payload["entries"] if e["entry_type"] == "discussion_context"]

        claims_path = output_path.with_name(output_path.stem + "_claims.json")
        context_path = output_path.with_name(output_path.stem + "_context.json")

        claims_data = {
            "source": str(input_path),
            "created_utc": data["created_utc"],
            "min_score": args.min_score,
            "entry_type": "explicit_parse_claim",
            "stats": {
                "entries_extracted": len(explicit),
                "refs_unique": len({r for e in explicit for r in e["refs"]}),
                "forms_unique": len({f for e in explicit for f in e["forms"]}),
                "high_confidence": sum(1 for e in explicit if e["confidence"] == "high"),
                "medium_confidence": sum(1 for e in explicit if e["confidence"] == "medium"),
                "low_confidence": sum(1 for e in explicit if e["confidence"] == "low"),
                "claim_strength_strong": sum(1 for e in explicit if e["claim_strength"] == "strong"),
                "claim_strength_moderate": sum(1 for e in explicit if e["claim_strength"] == "moderate"),
            },
            "entries": explicit,
        }
        context_data = {
            "source": str(input_path),
            "created_utc": data["created_utc"],
            "min_score": args.min_score,
            "entry_type": "discussion_context",
            "stats": {
                "entries_extracted": len(context),
                "refs_unique": len({r for e in context for r in e["refs"]}),
                "forms_unique": len({f for e in context for f in e["forms"]}),
                "high_confidence": sum(1 for e in context if e["confidence"] == "high"),
                "medium_confidence": sum(1 for e in context if e["confidence"] == "medium"),
                "low_confidence": sum(1 for e in context if e["confidence"] == "low"),
                "claim_strength_weak_or_none": sum(
                    1 for e in context if e["claim_strength"] in {"weak", "none"}
                ),
            },
            "entries": context,
        }
        claims_path.write_text(json.dumps(claims_data, ensure_ascii=False, indent=2), encoding="utf-8")
        context_path.write_text(json.dumps(context_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"Wrote {payload['stats']['entries_extracted']} entries to {output_path} "
        f"(unique refs: {payload['stats']['refs_unique']}, unique forms: {payload['stats']['forms_unique']})"
    )
    if args.split_output:
        print(
            f"Wrote split files: {claims_path} ({len(explicit)}), "
            f"{context_path} ({len(context)})"
        )


if __name__ == "__main__":
    main()
