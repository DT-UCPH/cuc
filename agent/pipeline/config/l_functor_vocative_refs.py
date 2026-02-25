"""Reference-based context rules for `l(III)` and `l(IV)` disambiguation."""

from __future__ import annotations

import re

from pipeline.config.l_negation_exception_refs import normalize_ktu_ref

_KTU_REF_KEY_RE = re.compile(
    r"^(?:KTU|CAT)\s+(?P<tablet>\d+\.\d+)(?:\s+(?P<section>[IVX]+))?(?:\s*:\s*|\s+)(?P<line>\d+)$",
    flags=re.IGNORECASE,
)

_L_III_REFS = (
    "KTU 1.1 V:27",
    "KTU 1.2 I:31",
    "KTU 1.2 IV:32",
    "KTU 1.3 V:35",
    "KTU 1.4 III:21",
    "KTU 1.4 IV:20",
    "KTU 1.4 V:3",
    "KTU 1.4 V:4",
    "KTU 1.4 VII:50",
    "KTU 1.5 I:6",
    "KTU 1.6 II:26",
    "KTU 1.6 II:35",
    "KTU 1.6 V:7",
    "KTU 1.6 VI:27",
    "KTU 1.9:12",
    "KTU 1.15 II:10",
    "KTU 1.15 V:18",
    "KTU 1.16 I:4",
    "KTU 1.17 I:23",
    "KTU 1.17 VI:43",
    "KTU 1.19 II:33",
    "KTU 1.19 III:40",
    "KTU 1.21 II:4",
    "KTU 1.24:36",
    "KTU 1.88:3",
    "KTU 2.61:9",
    "KTU 2.72:20",
)

_L_IV_REFS = (
    "KTU 1.2 IV:8",
    "KTU 1.2 IV:28",
    "KTU 1.3 VI:10",
    "KTU 1.4 V:59",
    "KTU 1.4 VII:23",
    "KTU 1.5 II:11",
    "KTU 1.6 I:45",
    "KTU 1.6 II:14",
    "KTU 1.6 III:23",
    "KTU 1.6 VI:24",
    "KTU 1.12 I:14",
    "KTU 1.13:22",
    "KTU 1.15 II:13",
    "KTU 1.16 IV:10",
    "KTU 1.16 VI:16",
    "KTU 1.16 VI:41",
    "KTU 1.17:42",
    "KTU 1.17 I:23",
    "KTU 1.17 VI:26",
    "KTU 1.19 II:41",
    "KTU 1.24:6",
    "KTU 1.24:15",
    "KTU 1.24:24",
    "KTU 1.92:39",
)


def canonical_ktu_ref_key(ref: str | None) -> str | None:
    """Normalize a KTU/CAT section label to a section-aware canonical key."""
    label = normalize_ktu_ref(ref)
    if not label:
        return None
    match = _KTU_REF_KEY_RE.match(label)
    if not match:
        return None
    tablet = match.group("tablet")
    section = (match.group("section") or "").upper()
    line_no = int(match.group("line"))
    if section:
        return f"{tablet} {section}:{line_no}"
    return f"{tablet}:{line_no}"


_L_III_REF_KEYS = frozenset(
    key for key in (canonical_ktu_ref_key(item) for item in _L_III_REFS) if key is not None
)
_L_IV_REF_KEYS = frozenset(
    key for key in (canonical_ktu_ref_key(item) for item in _L_IV_REFS) if key is not None
)


def expected_l_homonym_for_ref(section_ref: str | None, next_has_verb: bool) -> str | None:
    """Return expected homonym (`III`/`IV`) for a section/context, if constrained."""
    key = canonical_ktu_ref_key(section_ref)
    if key is None:
        return None

    in_iii = key in _L_III_REF_KEYS
    in_iv = key in _L_IV_REF_KEYS

    if in_iii and in_iv:
        return "III" if next_has_verb else "IV"
    if in_iii:
        return "III"
    if in_iv:
        return None if next_has_verb else "IV"
    return None
