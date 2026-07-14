"""Propagate richer option sets to parallel rows with the same surface form."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Set, Tuple

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow, parse_tsv_line

VariantTuple = Tuple[str, str, str, str]
_ROOT_RE = re.compile(r"^/([^/]+)/")


def _split_variants(value: str) -> List[str]:
    return [v.strip() for v in (value or "").split(";") if v.strip()]


def _aligned_variants(
    analysis: str,
    dulat: str,
    pos: str,
    gloss: str,
) -> Tuple[VariantTuple, ...]:
    """Return aligned option tuples for columns 3-6, or empty tuple if malformed."""
    columns = [
        _split_variants(analysis),
        _split_variants(dulat),
        _split_variants(pos),
        _split_variants(gloss),
    ]
    counts = [len(col) for col in columns]
    if any(count == 0 for count in counts):
        return ()
    if len(set(counts)) != 1:
        return ()
    return tuple(zip(columns[0], columns[1], columns[2], columns[3]))


def _split_gloss_senses(gloss: str) -> List[str]:
    return [x.strip() for x in (gloss or "").split("/") if x.strip()]


def _extract_root_final_radical(dulat: str) -> str:
    token = (dulat or "").split(",", 1)[0].strip()
    m = _ROOT_RE.match(token)
    if not m:
        return ""
    parts = [p.strip() for p in m.group(1).split("-") if p.strip()]
    if len(parts) != 3:
        return ""
    return parts[-1]


def _normalize_variant_for_root_alignment(variant: VariantTuple) -> VariantTuple:
    analysis, dulat, pos, gloss = variant
    if "vb" not in (pos or ""):
        return variant
    if "[" not in analysis or "/" in analysis:
        return variant
    if "(w&y[" in analysis:
        return variant
    if not analysis.endswith("y["):
        return variant
    if _extract_root_final_radical(dulat) != "w":
        return variant
    return (analysis[:-2] + "(w&y[", dulat, pos, gloss)


def _canonicalize_variants(variants: Tuple[VariantTuple, ...]) -> Tuple[VariantTuple, ...]:
    """Normalize one aligned variant set.

    - apply weak-final root/analysis normalization where root-final `w` is
      represented by surface `y` in prefix forms as `(w&y`.
    - collapse duplicate `(analysis, dulat, pos)` options and merge glosses with `/`.
    - when multiple analyses point to same `(dulat, pos)`, harmonize glosses
      to one `/`-joined sense set for all of them.
    """
    if not variants:
        return ()

    normalized = [_normalize_variant_for_root_alignment(v) for v in variants]

    by_key3: Dict[Tuple[str, str, str], List[str]] = {}
    key3_order: List[Tuple[str, str, str]] = []
    for analysis, dulat, pos, gloss in normalized:
        key3 = (analysis, dulat, pos)
        if key3 not in by_key3:
            by_key3[key3] = []
            key3_order.append(key3)
        senses = by_key3[key3]
        for sense in _split_gloss_senses(gloss):
            if sense not in senses:
                senses.append(sense)

    by_key2: Dict[Tuple[str, str], List[str]] = {}
    for analysis, dulat, pos in key3_order:
        key2 = (dulat, pos)
        if key2 not in by_key2:
            by_key2[key2] = []
        senses = by_key2[key2]
        for sense in by_key3[(analysis, dulat, pos)]:
            if sense not in senses:
                senses.append(sense)

    out: List[VariantTuple] = []
    seen: Set[VariantTuple] = set()
    for analysis, dulat, pos in key3_order:
        key2 = (dulat, pos)
        gloss = "/".join(by_key2[key2]) if by_key2[key2] else ""
        item = (analysis, dulat, pos, gloss)
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return tuple(out)


def _variant_head(variant: VariantTuple) -> Tuple[str, str, str]:
    return variant[0], variant[1], variant[2]


@dataclass(frozen=True)
class SurfacePayload:
    """Canonical aligned col3-col6 payload for one surface token."""

    variants: Tuple[VariantTuple, ...]
    analysis: str
    dulat: str
    pos: str
    gloss: str
    source_rows: int

    @property
    def variant_count(self) -> int:
        return len(self.variants)


class SurfaceOptionPropagationFixer(RefinementStep):
    """Copy richer aligned options to rows that currently have fewer options.

    This is a conservative propagation step:
    - only surfaces with length >= `min_surface_len`,
    - only aligned multi-option payloads (same option count in col3-col6),
    - only when target row shares at least one DULAT token with canonical payload.
    """

    def __init__(
        self,
        corpus_dir: Path,
        file_glob: str = "KTU 1.*.tsv",
        min_surface_len: int = 3,
        allowed_surfaces: Iterable[str] | None = None,
    ) -> None:
        self._min_surface_len = min_surface_len
        self._allowed_surfaces: Set[str] | None = (
            {s.strip() for s in allowed_surfaces if s and s.strip()}
            if allowed_surfaces is not None
            else None
        )
        self._payload_by_surface = self._build_payload_index(
            corpus_dir=corpus_dir, file_glob=file_glob
        )

    @property
    def name(self) -> str:
        return "surface-option-propagation"

    def refine_row(self, row: TabletRow) -> TabletRow:
        surface = (row.surface or "").strip()
        if len(surface) < self._min_surface_len:
            return row
        if self._allowed_surfaces is not None and surface not in self._allowed_surfaces:
            return row

        payload = self._payload_by_surface.get(surface)
        if payload is None:
            return row

        current_variants = _aligned_variants(row.analysis, row.dulat, row.pos, row.gloss)
        if not current_variants:
            return row
        current_variants = _canonicalize_variants(current_variants)
        current_row = TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(item[0] for item in current_variants),
            dulat=";".join(item[1] for item in current_variants),
            pos=";".join(item[2] for item in current_variants),
            gloss=";".join(item[3] for item in current_variants),
            comment=row.comment,
        )

        # High-confidence requirement: existing row must be an aligned subset of
        # the canonical payload's aligned option tuples.
        is_subset = {_variant_head(v) for v in current_variants}.issubset(
            {_variant_head(v) for v in payload.variants}
        )
        if not is_subset:
            return current_row

        # If row already carries at least as many variants, still allow a rewrite
        # when payload provides canonicalized equivalents (for example merged glosses).
        if len(current_variants) >= payload.variant_count:
            if (
                current_row.analysis == payload.analysis
                and current_row.dulat == payload.dulat
                and current_row.pos == payload.pos
                and current_row.gloss == payload.gloss
            ):
                return current_row

        return TabletRow(
            line_id=current_row.line_id,
            surface=current_row.surface,
            analysis=payload.analysis,
            dulat=payload.dulat,
            pos=payload.pos,
            gloss=payload.gloss,
            comment=current_row.comment,
        )

    def _build_payload_index(self, corpus_dir: Path, file_glob: str) -> Dict[str, SurfacePayload]:
        by_surface: Dict[str, SurfacePayload] = {}
        by_surface_payload_counts: Dict[str, Dict[Tuple[VariantTuple, ...], int]] = {}
        for path in sorted(corpus_dir.glob(file_glob)):
            for raw in path.read_text(encoding="utf-8").splitlines():
                if not raw or raw.lstrip().startswith("#"):
                    continue
                row = parse_tsv_line(raw)
                if row is None:
                    continue
                if row.analysis.strip() == "?":
                    continue

                surface = (row.surface or "").strip()
                if len(surface) < self._min_surface_len:
                    continue
                if self._allowed_surfaces is not None and surface not in self._allowed_surfaces:
                    continue

                raw_variants = _aligned_variants(
                    row.analysis,
                    row.dulat,
                    row.pos,
                    row.gloss,
                )
                if len(raw_variants) <= 1:
                    continue
                variants = _canonicalize_variants(raw_variants)
                if len(variants) == 0:
                    continue
                if not self._variants_reconstruct_to_surface(variants, surface):
                    continue

                counters = by_surface_payload_counts.setdefault(surface, {})
                counters[variants] = counters.get(variants, 0) + 1
        for surface, payload_counts in by_surface_payload_counts.items():
            payload = self._select_canonical_payload(payload_counts)
            if payload is not None:
                by_surface[surface] = payload
        return by_surface

    def _select_canonical_payload(
        self,
        payload_counts: Mapping[Tuple[VariantTuple, ...], int],
    ) -> SurfacePayload | None:
        if not payload_counts:
            return None
        max_variants = max(len(variants) for variants in payload_counts)
        richest = [variants for variants in payload_counts if len(variants) == max_variants]
        if len(richest) != 1:
            return None
        selected = richest[0]
        return SurfacePayload(
            variants=selected,
            analysis=";".join(item[0] for item in selected),
            dulat=";".join(item[1] for item in selected),
            pos=";".join(item[2] for item in selected),
            gloss=";".join(item[3] for item in selected),
            source_rows=payload_counts[selected],
        )

    def _variants_reconstruct_to_surface(
        self,
        variants: Tuple[VariantTuple, ...],
        surface: str,
    ) -> bool:
        expected = normalize_surface(surface)
        for analysis, _dulat, _pos, _gloss in variants:
            reconstructed = normalize_surface(reconstruct_surface_from_analysis(analysis))
            if reconstructed != expected:
                return False
        return True
