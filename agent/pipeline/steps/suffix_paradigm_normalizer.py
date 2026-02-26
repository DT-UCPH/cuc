"""Normalize suffix/enclitic markers in col3 to paradigm-safe encoding."""

from __future__ import annotations

import re

from pipeline.steps.base import RefinementStep, TabletRow

# From tagging conventions: these clitic/suffix segments should be encoded
# without homonym numerals in col3 (e.g., +n, +ny, +h=, ~n, [n=).
_PRONOMINAL_SEGMENTS = (
    "nkm",
    "ny",
    "nk",
    "nh",
    "nn",
    "km",
    "kn",
    "hm",
    "hn",
    "y",
    "n",
    "k",
    "h",
)

_HOMONYM_MARKED_SUFFIX_RE = re.compile(
    r"(?P<marker>[+~\[])(?P<seg>"
    + "|".join(_PRONOMINAL_SEGMENTS)
    + r")(?:(?P<eq1>=)?(?P<hom>\([IVX]+\))(?P<eq2>=)?)"
)


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


class SuffixParadigmNormalizer(RefinementStep):
    """Drop homonym numerals from suffix/enclitic markers in analysis variants."""

    @property
    def name(self) -> str:
        return "suffix-paradigm-normalizer"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row

        changed = False
        out: list[str] = []

        for variant in analysis_variants:
            rewritten = self._normalize_variant(variant)
            if rewritten != variant:
                changed = True
            out.append(rewritten)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(out),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _normalize_variant(self, variant: str) -> str:
        text = (variant or "").strip()
        if not text or text == "?":
            return text

        def repl(match: re.Match[str]) -> str:
            marker = match.group("marker")
            segment = match.group("seg")
            eq = "=" if (match.group("eq1") or match.group("eq2")) else ""
            return f"{marker}{segment}{eq}"

        return _HOMONYM_MARKED_SUFFIX_RE.sub(repl, text)
