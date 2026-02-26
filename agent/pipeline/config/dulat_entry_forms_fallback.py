"""Fallback extraction of DULAT form tokens from entry HTML text."""

from __future__ import annotations

import re

from pipeline.config.dulat_form_text_overrides import LOOKUP_NORMALIZE

_FORMS_BLOCK_RE = re.compile(
    r"(?:<b>)?\s*¶?\s*Forms?\s*:\s*(?:</b>)?(?P<body>.*?)(?=(?:<br>\s*<b>|<b>|$))",
    flags=re.IGNORECASE | re.DOTALL,
)
_ITALIC_TOKEN_RE = re.compile(r"<i>\s*([^<]+?)\s*</i>", flags=re.IGNORECASE)
_ITALIC_WORD_BREAK_JOIN_RE = re.compile(
    r"<i>\s*([^<]+?)\s*</i>\s*\{\s*\.\s*\}\s*<i>\s*([^<]+?)\s*</i>",
    flags=re.IGNORECASE,
)
_ITALIC_RESTORATION_JOIN_RE = re.compile(
    r"<i>\s*([^<]+?)\s*</i>\s*&lt;\s*<i>\s*([^<]+?)\s*</i>\s*&gt;\s*<i>\s*([^<]+?)\s*</i>",
    flags=re.IGNORECASE,
)
_PREV_TOKEN_RE = re.compile(r"([A-Za-z0-9À-ÖØ-öø-ÿŠṮṯḫḥḏẓʿʕʔ/\\-]+\.?)\s*$")
_ABBR_INDEX = frozenset(
    {
        "sg",
        "sg.",
        "pl",
        "pl.",
        "du",
        "du.",
        "m",
        "m.",
        "f",
        "f.",
        "abs",
        "abs.",
        "cstr",
        "cstr.",
        "suff",
        "suff.",
        "suffc",
        "suffc.",
        "prefc",
        "prefc.",
        "impv",
        "impv.",
        "inf",
        "inf.",
        "ptc",
        "ptc.",
        "opt",
        "opt.",
        "juss",
        "juss.",
        "g",
        "g.",
        "d",
        "d.",
        "n",
        "n.",
        "r",
        "r.",
        "l",
        "l.",
        "š",
        "š.",
        "gt",
        "gt.",
        "dt",
        "dt.",
        "lt",
        "lt.",
        "pass",
        "pass.",
        "allom",
        "allom.",
    }
)


def _normalize_lookup(text: str) -> str:
    return (text or "").strip().translate(LOOKUP_NORMALIZE)


def _clean_form_token(token: str) -> str:
    """Keep Unicode letter inventory intact when normalizing fallback forms."""
    return "".join(ch for ch in (token or "") if ch.isalpha() or ch == "-")


def _merge_word_break_italic_tokens(html_text: str) -> str:
    """Join split italic forms such as `<i>ytn</i>{.}<i>hm</i>` -> `<i>ytnhm</i>`."""
    body = html_text
    while True:
        body, n_subs = _ITALIC_WORD_BREAK_JOIN_RE.subn(
            lambda m: f"<i>{m.group(1)}{m.group(2)}</i>",
            body,
        )
        if n_subs == 0:
            break
    while True:
        body, n_subs = _ITALIC_RESTORATION_JOIN_RE.subn(
            lambda m: f"<i>{m.group(1)}{m.group(2)}{m.group(3)}</i>",
            body,
        )
        if n_subs == 0:
            return body


def _looks_like_forms_continuation(text_tail: str) -> bool:
    plain = re.sub(r"^(?:\s|<[^>]+>)+", "", text_tail or "")
    if not plain:
        return False
    return bool(
        re.match(
            (
                r"^(?:"
                r"(?:G|D|N|R|L|Š|Gt|Dt|Lt|tD|tL|N/Gpass\.?|Gpass\.?|Dpass\.?|Špass\.?)\s+"
                r")?"
                r"(?:suffc?\.?|prefc?\.?|impv\.?|inf\.?|ptc\.?|opt\.?|juss\.?|sg\.?|pl\.?|du\.?)\b"
            ),
            plain,
            flags=re.IGNORECASE,
        )
    )


def _truncate_forms_body(html_text: str) -> str:
    """Trim the forms block at the first terminal sentence boundary.

    Stops at the first non-abbreviation period after at least one `<i>...</i>`
    token has been seen, unless the period is followed by punctuation that
    implies continuation.
    """
    text = html_text or ""
    depth = 0
    curly_depth = 0
    seen_form = False
    i = 0
    while i < len(text):
        if text.startswith("<b>", i):
            return text[:i] if seen_form else text
        if text.startswith("<i>", i):
            seen_form = True
        if text[i] == "<":
            close_idx = text.find(">", i)
            if close_idx == -1:
                break
            i = close_idx + 1
            continue

        ch = text[i]
        if ch in "([":
            depth += 1
        elif ch == "{":
            curly_depth += 1
        elif ch in ")]" and depth > 0:
            depth -= 1
        elif ch == "}" and curly_depth > 0:
            curly_depth -= 1
        elif ch == "." and depth == 0 and curly_depth == 0 and seen_form:
            prev_match = _PREV_TOKEN_RE.search(text[:i])
            prev_token = (prev_match.group(1).rstrip(".").lower() if prev_match else "").strip()
            if prev_token and (prev_token in _ABBR_INDEX):
                i += 1
                continue
            if _looks_like_forms_continuation(text[i + 1 :]):
                i += 1
                continue
            next_match = re.search(r"\S", text[i + 1 :])
            next_ch = next_match.group(0) if next_match else ""
            if next_ch in {",", ";", ":"}:
                i += 1
                continue
            return text[: i + 1]
        i += 1
    return text


def extract_forms_from_entry_text(entry_text: str) -> tuple[str, ...]:
    """Extract candidate form tokens from the raw `¶ Forms:` HTML block.

    This fallback is used when the structured `forms` table missed items during
    source parsing. It only keeps short single-token italic payloads from the
    forms paragraph.
    """
    text = (entry_text or "").strip()
    if not text:
        return tuple()
    match = _FORMS_BLOCK_RE.search(text)
    if not match:
        return tuple()
    body = match.group("body") or ""
    if not body:
        return tuple()

    truncated_body = _truncate_forms_body(body)

    out: list[str] = []
    seen: set[str] = set()
    merged_body = _merge_word_break_italic_tokens(truncated_body)
    for raw in _ITALIC_TOKEN_RE.findall(merged_body):
        token = (raw or "").strip()
        token = re.sub(r"\s+", " ", token)
        token = token.strip(".,;:!?")
        if not token or " " in token:
            continue
        cleaned = _clean_form_token(token)
        if not cleaned or len(cleaned) < 2:
            continue
        key = _normalize_lookup(cleaned)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return tuple(out)
