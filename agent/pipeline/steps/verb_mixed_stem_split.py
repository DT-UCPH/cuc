"""Split mixed-stem verb POS options into aligned semicolon variants.

When one verbal row carries slash-delimited POS options with different stem
signatures, downstream stem-marker fixers currently union those requirements
onto one analysis. This step separates those signatures first so later steps
can normalize each variant independently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.steps.base import RefinementStep, TabletRow

_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)
_VERBAL_NOUN_POS_RE = re.compile(r"\bvb\.\s*n\.", flags=re.IGNORECASE)
_POS_STEM_RE = re.compile(r"\b(Gpass|Dpass|Lpass|Špass|Gt|Dt|Lt|Nt|tD|tL|Št|G|D|L|N|R|Š)\b")
_PREFORMATIVE_RE = re.compile(r"^(?:![ytan](?:=+)?!|!\(ʔ&[aiu]!)", flags=re.IGNORECASE)
_MARKER_ORDER = (":d", ":l", ":r", ":pass")


def _split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def _split_slash_options(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*/\s*", (value or "").strip()) if part.strip()]


def _variant_value(values: list[str], index: int) -> str:
    if index < len(values):
        return values[index]
    if len(values) == 1:
        return values[0]
    return ""


def _is_target_pos(pos_text: str) -> bool:
    text = (pos_text or "").strip()
    if not _VB_POS_HEAD_RE.search(text):
        return False
    if _VERBAL_NOUN_POS_RE.search(text):
        return False
    return True


def _extract_stems(pos_text: str) -> set[str]:
    return set(_POS_STEM_RE.findall(pos_text or ""))


def _required_markers(stems: set[str]) -> tuple[str, ...]:
    markers: list[str] = []
    if stems & {"D", "Dt", "tD"}:
        markers.append(":d")
    if stems & {"L", "Lt", "tL"}:
        markers.append(":l")
    if "R" in stems:
        markers.append(":r")
    if stems & {"Gpass", "Dpass", "Lpass", "Špass"}:
        markers.append(":pass")
    return tuple(markers)


def _requires_n_assimilation(stems: set[str]) -> bool:
    return "N" in stems


def _join_options(options: list[str]) -> str:
    return " / ".join(option for option in options if option)


def _strip_disallowed_markers(analysis: str, keep_markers: tuple[str, ...]) -> str:
    text = (analysis or "").strip()
    if "[" not in text:
        return text

    head, tail = text.split("[", 1)
    clitic_index = len(tail)
    for marker in ("+", "~"):
        idx = tail.find(marker)
        if idx >= 0:
            clitic_index = min(clitic_index, idx)

    core = tail[:clitic_index]
    suffix = tail[clitic_index:]
    for marker in _MARKER_ORDER:
        if marker not in keep_markers:
            core = core.replace(marker, "")
    return f"{head}[{core}{suffix}"


def _strip_assimilated_n_marker(analysis: str) -> str:
    text = (analysis or "").strip()
    match = _PREFORMATIVE_RE.match(text)
    if match is None:
        return text

    prefix_end = match.end()
    tail = text[prefix_end:]
    for marker in ("(]n]", "]n]", "](n]"):
        if tail.startswith(marker):
            return f"{text[:prefix_end]}{tail[len(marker) :]}"
    return text


@dataclass(frozen=True)
class _StemSignatureGroup:
    markers: tuple[str, ...]
    needs_n: bool
    options: list[str]


class VerbMixedStemSplitFixer(RefinementStep):
    """Split verb rows whose slash options require different stem signatures."""

    @property
    def name(self) -> str:
        return "verb-mixed-stem-split"

    def refine_row(self, row: TabletRow) -> TabletRow:
        pos_variants = _split_semicolon(row.pos)
        if not pos_variants:
            return row

        analysis_variants = _split_semicolon(row.analysis)
        dulat_variants = _split_semicolon(row.dulat)
        gloss_variants = _split_semicolon(row.gloss)

        paired = self._pair_preexpanded_analyses(
            row=row,
            analysis_variants=analysis_variants,
            dulat_variants=dulat_variants,
            pos_variants=pos_variants,
            gloss_variants=gloss_variants,
        )
        if paired is not None:
            return paired

        changed = False
        out_analysis: list[str] = []
        out_dulat: list[str] = []
        out_pos: list[str] = []
        out_gloss: list[str] = []

        variant_count = max(
            len(analysis_variants), len(dulat_variants), len(pos_variants), len(gloss_variants), 1
        )
        for idx in range(variant_count):
            analysis = _variant_value(analysis_variants, idx)
            dulat = _variant_value(dulat_variants, idx)
            pos = _variant_value(pos_variants, idx)
            gloss = _variant_value(gloss_variants, idx)

            if not _is_target_pos(pos):
                out_analysis.append(analysis)
                out_dulat.append(dulat)
                out_pos.append(pos)
                out_gloss.append(gloss)
                continue

            groups = self._signature_groups(pos)
            if not groups:
                out_analysis.append(analysis)
                out_dulat.append(dulat)
                out_pos.append(pos)
                out_gloss.append(gloss)
                continue

            if len(groups) > 1:
                changed = True

            for group in groups:
                normalized_analysis = _strip_disallowed_markers(analysis, group.markers)
                if not group.needs_n:
                    normalized_analysis = _strip_assimilated_n_marker(normalized_analysis)
                if normalized_analysis != analysis:
                    changed = True
                out_analysis.append(normalized_analysis)
                out_dulat.append(dulat)
                out_pos.append(_join_options(group.options))
                out_gloss.append(gloss)

        deduped: list[tuple[str, str, str, str]] = []
        for item in zip(out_analysis, out_dulat, out_pos, out_gloss):
            if item in deduped:
                changed = True
                continue
            deduped.append(item)

        final_analysis = "; ".join(item[0] for item in deduped)
        final_dulat = "; ".join(item[1] for item in deduped)
        final_pos = "; ".join(item[2] for item in deduped)
        final_gloss = "; ".join(item[3] for item in deduped)

        if (
            not changed
            and final_analysis == row.analysis
            and final_dulat == row.dulat
            and final_pos == row.pos
            and final_gloss == row.gloss
        ):
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=final_analysis,
            dulat=final_dulat,
            pos=final_pos,
            gloss=final_gloss,
            comment=row.comment,
        )

    def _pair_preexpanded_analyses(
        self,
        *,
        row: TabletRow,
        analysis_variants: list[str],
        dulat_variants: list[str],
        pos_variants: list[str],
        gloss_variants: list[str],
    ) -> TabletRow | None:
        if len(pos_variants) != 1:
            return None
        if len(analysis_variants) <= 1:
            return None
        if not _is_target_pos(pos_variants[0]):
            return None

        groups = self._signature_groups(pos_variants[0])
        if len(groups) <= 1 or len(groups) != len(analysis_variants):
            return None

        changed = False
        out_analysis: list[str] = []
        out_dulat: list[str] = []
        out_pos: list[str] = []
        out_gloss: list[str] = []

        for idx, group in enumerate(groups):
            analysis = analysis_variants[idx]
            normalized_analysis = _strip_disallowed_markers(analysis, group.markers)
            if not group.needs_n:
                normalized_analysis = _strip_assimilated_n_marker(normalized_analysis)
            if normalized_analysis != analysis:
                changed = True

            out_analysis.append(normalized_analysis)
            out_dulat.append(_variant_value(dulat_variants, idx))
            out_pos.append(_join_options(group.options))
            out_gloss.append(_variant_value(gloss_variants, idx))

        final_analysis = "; ".join(out_analysis)
        final_dulat = "; ".join(out_dulat)
        final_pos = "; ".join(out_pos)
        final_gloss = "; ".join(out_gloss)

        if (
            not changed
            and final_analysis == row.analysis
            and final_dulat == row.dulat
            and final_pos == row.pos
            and final_gloss == row.gloss
        ):
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=final_analysis,
            dulat=final_dulat,
            pos=final_pos,
            gloss=final_gloss,
            comment=row.comment,
        )

    def _signature_groups(self, pos_text: str) -> list[_StemSignatureGroup]:
        options = _split_slash_options(pos_text)
        if len(options) <= 1:
            if not options:
                return []
            stems = _extract_stems(options[0])
            return [
                _StemSignatureGroup(
                    markers=_required_markers(stems),
                    needs_n=_requires_n_assimilation(stems),
                    options=options,
                )
            ]

        grouped: list[_StemSignatureGroup] = []
        for option in options:
            stems = _extract_stems(option)
            signature = (_required_markers(stems), _requires_n_assimilation(stems))
            for index, group in enumerate(grouped):
                if (group.markers, group.needs_n) == signature:
                    grouped[index] = _StemSignatureGroup(
                        markers=group.markers,
                        needs_n=group.needs_n,
                        options=[*group.options, option],
                    )
                    break
            else:
                grouped.append(
                    _StemSignatureGroup(
                        markers=signature[0],
                        needs_n=signature[1],
                        options=[option],
                    )
                )
        return grouped
