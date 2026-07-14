"""Normalize prefixed III-aleph verb analyses to reconstructable encoding.

Example:
- surface `tḫṭu`, analysis `ḫṭʔ[u`, DULAT `/ḫ-ṭ-ʔ/`
  -> `!t!ḫṭ(ʔ[&u`
"""

from __future__ import annotations

import re

from pipeline.steps.analysis_utils import normalize_surface
from pipeline.steps.base import RefinementStep, TabletRow

_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)
_PREFORMATIVE_LETTERS = {"y", "t", "a", "n", "i", "u"}
_ROOT_FINAL_ALEPH_RE = re.compile(r"^/[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ-]+-ʔ/$")
_ANALYSIS_LETTER_RE = re.compile(r"[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ]")
_ANALYSIS_III_ALEPH_MISSING_PREFIX_RE = re.compile(
    r"^(?P<stem>[A-Za-zʔʕʿˤḫḥṭṣṯẓġḏšảỉủ\] \[]*ʔ)(?P<hom>\([IVX]+\))?\[(?P<infl>[aiu])$"
)


def _format_preformative_marker(letter: str) -> str:
    """Render canonical prefix-conjugation marker for one preformative letter."""
    preformative = (letter or "").strip()
    if preformative in {"a", "i", "u"}:
        return f"!(ʔ&{preformative}!"
    return f"!{preformative}!"


def _extract_letters(text: str) -> str:
    return "".join(ch for ch in (text or "") if _ANALYSIS_LETTER_RE.match(ch))


def _first_dulat_head(dulat_text: str) -> str:
    first_variant = (dulat_text or "").split(";", 1)[0].strip()
    first_slot = first_variant.split(",", 1)[0].strip()
    return first_slot


def _rewrite_prefixed_iii_aleph_variant(
    *,
    surface: str,
    analysis: str,
    dulat_head: str,
    pos: str,
) -> str:
    a_txt = (analysis or "").strip()
    if not a_txt or a_txt.startswith("!") or "[/" in a_txt:
        return analysis
    if not _VB_POS_HEAD_RE.search(pos or ""):
        return analysis
    if not _ROOT_FINAL_ALEPH_RE.match((dulat_head or "").strip()):
        return analysis

    m = _ANALYSIS_III_ALEPH_MISSING_PREFIX_RE.match(a_txt)
    if m is None:
        return analysis

    stem = m.group("stem")
    hom = m.group("hom") or ""
    inflection = m.group("infl")
    if not stem.endswith("ʔ"):
        return analysis

    surface_letters = _extract_letters(normalize_surface(surface))
    if len(surface_letters) < 2:
        return analysis
    preformative = surface_letters[0]
    if preformative not in _PREFORMATIVE_LETTERS:
        return analysis

    body = surface_letters[1:]
    if not body.endswith(inflection):
        return analysis
    visible_body = body[: -len(inflection)]
    expected_visible = _extract_letters(stem[:-1])
    if visible_body and expected_visible and not expected_visible.startswith(visible_body):
        return analysis

    stem_with_reconstructed_aleph = stem[:-1] + "(ʔ"
    marker = _format_preformative_marker(preformative)
    return f"{marker}{stem_with_reconstructed_aleph}{hom}[&{inflection}"


class PrefixedIIIAlephVerbFixer(RefinementStep):
    """Rewrite legacy III-aleph prefixed verb analyses to canonical form."""

    @property
    def name(self) -> str:
        return "prefixed-iii-aleph-verb"

    def refine_row(self, row: TabletRow) -> TabletRow:
        rewritten = _rewrite_prefixed_iii_aleph_variant(
            surface=row.surface,
            analysis=row.analysis,
            dulat_head=_first_dulat_head(row.dulat),
            pos=row.pos,
        )
        if rewritten == row.analysis:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=rewritten,
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )
