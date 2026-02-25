"""Config for high-confidence `l + X` prepositional bigram disambiguation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalSecondPayload:
    analysis: str
    dulat: str
    pos: str
    gloss: str


L_FORCE_I_BIGRAM_SURFACES = frozenset(
    {
        "arṣ",
        "špš",
        "mlkt",
        "ṣpn",
        "il",
        "kḥṯ",
        "ršp",
        "inš",
        "bˤlt",
        "ˤṯtrt",
        "ˤpr",
    }
)

L_BAAL_SURFACE = "bˤl"
L_BAAL_ANALYSIS = "bˤl(II)/"
L_BAAL_DULAT = "bʕl (II)"

L_PN_FAMILY_FORCE_I_SURFACES = frozenset(
    {
        "pn",
        "pnm",
        "pnh",
        "pnk",
        "pny",
        "pnwh",
        "pnnh",
        "pnṯk",
    }
)

L_PN_PREP_CANONICAL_PAYLOADS = {
    "pn": CanonicalSecondPayload(
        analysis="pn(m/",
        dulat="pnm",
        pos="n. m. pl. tant.",
        gloss="in front",
    ),
    "pnm": CanonicalSecondPayload(
        analysis="pn(m/m",
        dulat="pnm",
        pos="n. m. pl. tant.",
        gloss="in front",
    ),
    "pnh": CanonicalSecondPayload(
        analysis="pn(m/+h",
        dulat="pnm",
        pos="n. m. pl. tant.",
        gloss="in front",
    ),
    "pnk": CanonicalSecondPayload(
        analysis="pn(m/+k",
        dulat="pnm",
        pos="n. m. pl. tant.",
        gloss="in front",
    ),
    "pny": CanonicalSecondPayload(
        analysis="pn(m/+y",
        dulat="pnm",
        pos="n. m. pl. tant.",
        gloss="in front",
    ),
    "pnwh": CanonicalSecondPayload(
        analysis="pn&w(m/+h",
        dulat="pnm",
        pos="n. m. pl. tant.",
        gloss="in front",
    ),
}
