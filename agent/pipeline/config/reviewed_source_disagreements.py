"""Verified scholarly disagreements, not invalid morphology exceptions.

Keys include attestation and the complete lexical/POS analysis. These entries
only explain the named DULAT diagnostic in reviewed files; they neither admit
automatic candidates nor relax reconstruction, affix or schema checks.
"""


REVIEWED_SOURCE_DISAGREEMENTS = {
    (
        "KTU 1.5 I:26", "nšt", "nš(y[t=", "/n-š-y/", "vb G suffc. 2 m. sg.",
        "Non-G stem in DULAT requires stem marker",
    ): "EUPT G-SK 2 m. sg.; DULAT s.v. /n-š-y/ also records Del Olmo's precative G dissent",
    (
        "KTU 1.5 II:3", "lšn", "lšn/", "lšn", "n. m. sg.",
        "Noun POS gender mismatch for lšn: expected n. f., got n. m.",
    ): "EUPT at 1.5 II:3 gives masculine singular without a case; DULAT gives feminine",
}


def reviewed_disagreement_source(ref: str, parts: list[str], message: str) -> str | None:
    # parts has already had the reviewed sign-span field removed.
    if len(parts) != 7:
        return None
    key = (ref, parts[1], parts[2], parts[3], parts[4], message)
    return REVIEWED_SOURCE_DISAGREEMENTS.get(key)
