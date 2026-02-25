"""Reference-based exceptions for forced `l(II)` disambiguation."""

from __future__ import annotations

import re

_SEPARATOR_REF_RE = re.compile(r"^\s*#\s*(?:-+\s*)?((?:KTU|CAT)\s+.+?)\s*$", flags=re.IGNORECASE)
_KTU_1_3_IV_5_RE = re.compile(r"^(?:KTU|CAT)\s+1\.3\s+IV:5$", flags=re.IGNORECASE)
_KTU_4_348_1_RE = re.compile(r"^(?:KTU|CAT)\s+4\.348:1$", flags=re.IGNORECASE)
_KTU_4_213_SINGLE_RE = re.compile(r"^(?:KTU|CAT)\s+4\.213:(\d+)$", flags=re.IGNORECASE)
_KTU_4_213_RANGE_RE = re.compile(
    r"^(?:KTU|CAT)\s+4\.213:(\d+)\s*[–-]\s*(\d+)$",
    flags=re.IGNORECASE,
)


def normalize_ktu_ref(value: str | None) -> str:
    """Normalize KTU/CAT reference spacing for stable matching."""
    return re.sub(r"\s+", " ", (value or "").strip())


def extract_separator_ref(raw: str) -> str | None:
    """Extract KTU/CAT reference label from separator lines."""
    match = _SEPARATOR_REF_RE.match(raw or "")
    if not match:
        return None
    return normalize_ktu_ref(match.group(1))


def is_forced_l_negation_ref(ref: str | None) -> bool:
    """True when the ref belongs to DULAT `l(II)` noun/adj exception contexts."""
    label = normalize_ktu_ref(ref)
    if not label:
        return False
    if _KTU_1_3_IV_5_RE.match(label):
        return True
    if _KTU_4_348_1_RE.match(label):
        return True

    single = _KTU_4_213_SINGLE_RE.match(label)
    if single:
        line_no = int(single.group(1))
        return 2 <= line_no <= 23

    in_range = _KTU_4_213_RANGE_RE.match(label)
    if not in_range:
        return False
    start = int(in_range.group(1))
    end = int(in_range.group(2))
    if start > end:
        start, end = end, start
    return not (end < 2 or start > 23)
