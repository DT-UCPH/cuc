"""Forms for DULAT entries whose `forms` table rows are missing from the cache.

The pipeline discovers candidate entries for a surface purely through DULAT's
`forms` table (see `DulatGate._load_dulat_features`). An entry with no `forms`
rows is therefore invisible to the parser: it can never be proposed for any
surface, no matter what the entry itself says.

A handful of entries lost their forms during cache extraction. The effect is not
a missing gloss but a **silently wrong homonym choice** — the surviving homonym
wins unopposed. Supplement those entries here, keyed by (lemma, homonym) using
the same normalisation the gate applies to lemmas.

Only add an entry when DULAT's own text attests the form. This is a repair for a
cache defect, not a place to invent morphology.
"""

from __future__ import annotations

from typing import Dict, Tuple

from pipeline.config.dulat_form_text_overrides import LOOKUP_NORMALIZE


def _norm_lemma(value: str) -> str:
    return (value or "").translate(LOOKUP_NORMALIZE).strip()


def _norm_homonym(value: str) -> str:
    return (value or "").strip().upper()


# (lemma, homonym) -> ((form_text, morphology), ...)
_ENTRY_FORM_SUPPLEMENTS: Dict[Tuple[str, str], Tuple[Tuple[str, str], ...]] = {
    # ʕṯtrt (I) is the goddess Athtart; ʕṯtrt (II) is the toponym. The cache
    # holds forms only for (II) — and (I)'s summary is truncated to "DIŠ" —
    # so every one of the 35 ʕṯtrt tokens in the corpus was parsed as the
    # toponym, including the Baal cycle (1.2), the Athtart hunt (1.92), the
    # Ilu banquet (1.114) and the god lists (1.41, 1.47, 1.118). DULAT's own
    # (I) entry is headed `ʕṯtrt` and is cited for the DN throughout.
    ("ʕṯtrt", "I"): (("ʕṯtrt", ""),),
}

ENTRY_FORM_SUPPLEMENTS: Dict[Tuple[str, str], Tuple[Tuple[str, str], ...]] = {
    (_norm_lemma(lemma), _norm_homonym(hom)): forms
    for (lemma, hom), forms in _ENTRY_FORM_SUPPLEMENTS.items()
}


def supplemental_forms(lemma: str, homonym: str) -> Tuple[Tuple[str, str], ...]:
    """Return ((form_text, morphology), ...) to add for this entry, if any."""
    return ENTRY_FORM_SUPPLEMENTS.get((_norm_lemma(lemma), _norm_homonym(homonym)), ())
