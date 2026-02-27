"""Shared constants and normalization helpers for lint reports."""

from typing import Dict, List

MESSAGE_PREFIXES: List[str] = sorted(
    [
        "No DULAT entry found for lexeme/surface",
        "No DULAT entry found for clitic part:",
        "Missing DULAT entry token(s) in column 4",
        "Column 4 count must match analysis variant count",
        "Column 5 count must match analysis variant count",
        "Column 6 count should match analysis variant count",
        "Morphology placeholder '?' should use unresolved DULAT placeholder '?' in column 4",
        "Unresolved morphology placeholder '?' should use '?' or empty POS",
        "Unresolved morphology placeholder '?' should use '?' or empty gloss",
        "Unresolved DULAT placeholder '?' should also use '?' in morphology (column 3)",
        "Unresolved DULAT placeholder '?' should use '?' or empty POS",
        "Unresolved DULAT placeholder '?' should use '?' or empty gloss",
        "POS tokens must map to existing DULAT tokens in column 4",
        "Gloss tokens must map to existing DULAT tokens in column 4",
        "Empty DULAT token in column 4",
        "Unknown DULAT token in column 4:",
        "DULAT comment does not match candidates",
        "POS ambiguous in DULAT:",
        "POS token",
        "Disallowed character in columns 2-3:",
        "Analysis does not reconstruct to surface",
        "Each reconstructed letter must be prefixed by '('",
        "ʔ must be preceded by '(' in column 3",
        "Noun/adjective lacks '/' ending",
        "Verb lacks '[' ending",
        "Deverbal form matches both verb and noun entries in DULAT",
        "Deverbal form marked with '[' but only noun entry found in DULAT",
        "Non-G stem in DULAT requires stem marker",
        "Š stem marker present but DULAT lacks Š/Št/Špass",
        "Xt stem marker present but DULAT lacks *t stem",
        "D stem marker present but DULAT lacks D/Dt",
        "Suffixed pronominal form in DULAT should use '+' in analysis",
        "Suffix form without '+'",
        "Plural form missing split ending",
        "Feminine plural noun in DULAT should use '/t='",
        "Feminine plural noun in DULAT should be tagged with '/t='",
        "Feminine adjective/participle in DULAT should mark '-t' explicitly",
        "Feminine plural adjective/participle in DULAT should use '/t='",
        "Plurale tantum noun ending in '-t' should mark plural with '/t='",
        "Plurale tantum noun ending in '-m' should mark plural with '/m'",
        "Multiple DULAT candidates for lexeme:",
        "Multiple DULAT candidates for surface:",
        "Surface not found in UDB concordance",
        "Surface ",
        "Repeated ",
        "TODO/uncertain marker in comment:",
    ],
    key=len,
    reverse=True,
)

NORMALIZATION_MAP: Dict[str, str] = {
    "POS ambiguous in DULAT:": "POS ambiguous in DULAT",
    "Unknown DULAT token in column 4:": "Unknown DULAT token in column 4",
    "No DULAT entry found for clitic part:": "No DULAT entry found for clitic part",
    "Multiple DULAT candidates for lexeme:": "Multiple DULAT candidates for lexeme",
    "Multiple DULAT candidates for surface:": "Multiple DULAT candidates for surface",
    "TODO/uncertain marker in comment:": "TODO/uncertain marker in comment",
}


def normalize_message(msg: str) -> str:
    """Normalize variable issue text into stable buckets."""
    if msg.startswith("POS token "):
        return "POS token not allowed for declared DULAT entry"
    for prefix, normalized in NORMALIZATION_MAP.items():
        if msg.startswith(prefix):
            return normalized
    if msg.startswith("Surface ") and " parsed inconsistently:" in msg:
        return "Surface parsed inconsistently across IDs"
    if msg.startswith("Repeated ") and "has inconsistent col3-col6 payload across parallels:" in msg:
        return "Repeated sequence has inconsistent col3-col6 payload across parallels"
    if msg.startswith("Analysis does not reconstruct to surface"):
        return "Analysis does not reconstruct to surface"
    return msg
