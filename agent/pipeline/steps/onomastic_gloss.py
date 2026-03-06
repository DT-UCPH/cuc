"""Apply onomastic gloss overrides and canonical ʾ/ʿ transliteration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

from pipeline.dulat_attestation_index import DulatAttestationIndex
from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    normalize_separator_row,
    parse_tsv_line,
)
from pipeline.steps.onomastic_overrides import OnomasticOverrideStore
from project_paths import get_project_paths
from scripts.refine_results_mentions import parse_separator_ref

_ONOMASTIC_POS_TAGS = ("DN", "PN", "TN", "MN", "GN")
_ONOMASTIC_CHAR_MAP = str.maketrans(
    {
        "ʔ": "ʾ",
        "ˀ": "ʾ",
        "ʕ": "ʿ",
        "ˁ": "ʿ",
    }
)
_TRAILING_HOMONYM_RE = re.compile(r"\s*\(([IVX]+)\)\s*$")


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


def _join_comma(values: list[str]) -> str:
    return ", ".join(value.strip() for value in values)


def _join_semicolon(values: list[str]) -> str:
    return "; ".join(value.strip() for value in values)


class OnomasticGlossOverrideFixer(RefinementStep):
    """Override name glosses from a centralized source file."""

    def __init__(
        self,
        overrides_path: Path | None = None,
        overrides: Dict[str, str] | None = None,
        attestation_index: DulatAttestationIndex | None = None,
    ) -> None:
        self._overrides_path = overrides_path or (
            get_project_paths(Path(__file__).resolve()).data_sources_dir
            / "onomastic_gloss_overrides.tsv"
        )
        self._attestation_index = attestation_index or DulatAttestationIndex.empty()
        if overrides is not None:
            self._store = OnomasticOverrideStore.from_gloss_map(overrides)
        else:
            self._store = OnomasticOverrideStore.from_tsv(self._overrides_path)

    @property
    def name(self) -> str:
        return "onomastic-gloss-override"

    def refine_row(self, row: TabletRow) -> TabletRow:
        return self._refine_row(row, current_ref="")

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        rows_processed = 0
        rows_changed = 0
        current_ref = ""

        for raw in lines:
            if not raw.strip():
                out_lines.append(raw)
                continue
            if is_separator_line(raw):
                parsed_ref = parse_separator_ref(raw)
                if parsed_ref:
                    current_ref = parsed_ref
                out_lines.append(normalize_separator_row(raw))
                continue

            row = parse_tsv_line(raw)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            refined = self._refine_row(row, current_ref=current_ref)
            new_line = refined.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _refine_row(self, row: TabletRow, *, current_ref: str) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)
        gloss_variants = _split_semicolon(row.gloss)
        if not gloss_variants:
            return row

        n = len(gloss_variants)
        if len(analysis_variants) != n or len(dulat_variants) != n or len(pos_variants) != n:
            transformed = self._apply_variant_override(
                dulat_variant=row.dulat.strip(),
                pos_variant=row.pos.strip(),
                gloss_variant=row.gloss.strip(),
            )
            if transformed == row.gloss.strip():
                return row
            return TabletRow(
                line_id=row.line_id,
                surface=row.surface,
                analysis=row.analysis,
                dulat=row.dulat,
                pos=row.pos,
                gloss=transformed,
                comment=row.comment,
            )

        out_analysis: list[str] = []
        out_dulat: list[str] = []
        out_pos: list[str] = []
        out_gloss: list[str] = []
        changed = False
        existing_variant_keys: set[tuple[str, str, str]] = set()
        for i in range(n):
            existing_variant_keys.add(
                (
                    analysis_variants[i].strip(),
                    dulat_variants[i].strip(),
                    pos_variants[i].strip(),
                )
            )

        for i in range(n):
            analysis_variant = analysis_variants[i].strip()
            dulat_variant = dulat_variants[i].strip()
            pos_variant = pos_variants[i].strip()
            transformed = self._apply_variant_override(
                dulat_variant=dulat_variant,
                pos_variant=pos_variant,
                gloss_variant=gloss_variants[i],
            )
            has_other_viable_option = self._has_non_onomastic_viable_option(pos_variants)
            appended = self._appended_onomastic_variant(
                current_ref=current_ref,
                surface=row.surface,
                analysis_variant=analysis_variant,
                dulat_variant=dulat_variant,
                pos_variant=pos_variant,
                gloss_variant=transformed,
                existing_keys=existing_variant_keys,
                has_other_viable_option=has_other_viable_option,
            )
            if appended is not None:
                appended_key = (appended.analysis, appended.dulat, appended.pos)
                if appended_key not in existing_variant_keys:
                    out_analysis.append(appended.analysis)
                    out_dulat.append(appended.dulat)
                    out_pos.append(appended.pos)
                    out_gloss.append(appended.gloss)
                    existing_variant_keys.add(appended_key)
                    changed = True
            out_analysis.append(analysis_variant)
            out_dulat.append(dulat_variant)
            out_pos.append(pos_variant)
            out_gloss.append(transformed)
            if transformed != gloss_variants[i]:
                changed = True

        if not changed:
            return row
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=_join_semicolon(out_analysis),
            dulat=_join_semicolon(out_dulat),
            pos=_join_semicolon(out_pos),
            gloss=_join_semicolon(out_gloss),
            comment=row.comment,
        )

    def _apply_variant_override(
        self, dulat_variant: str, pos_variant: str, gloss_variant: str
    ) -> str:
        dulat_variant = dulat_variant.strip()
        pos_variant = pos_variant.strip()
        gloss_variant = gloss_variant.strip()
        onomastic_variant = self._is_onomastic_pos(pos_variant)
        override_gloss = self._store.get_gloss(dulat_variant)
        if override_gloss and onomastic_variant:
            return override_gloss

        dulat_slots = _split_comma(dulat_variant)
        pos_slots = _split_comma(pos_variant)
        slot_count = max(len(dulat_slots), len(pos_slots))
        if slot_count <= 1:
            if onomastic_variant:
                return self._normalize_onomastic_chars(gloss_variant)
            return gloss_variant

        gloss_slots = _split_comma(gloss_variant)
        if len(gloss_slots) != slot_count:
            # Conservative fallback: if slot alignment is uncertain, only apply
            # whole-variant normalization for clear onomastic POS values.
            if onomastic_variant:
                return self._normalize_onomastic_chars(gloss_variant)
            return gloss_variant

        changed = False
        for i in range(slot_count):
            d_slot = dulat_slots[i].strip() if i < len(dulat_slots) else ""
            p_slot = pos_slots[i].strip() if i < len(pos_slots) else ""
            g_slot = gloss_slots[i].strip()

            onomastic_slot = self._is_onomastic_pos(p_slot)
            override_slot = self._store.get_gloss(d_slot)
            if override_slot and onomastic_slot:
                new_slot = override_slot
            elif onomastic_slot:
                new_slot = self._normalize_onomastic_chars(g_slot)
            else:
                new_slot = g_slot
            if new_slot != g_slot:
                changed = True
            gloss_slots[i] = new_slot

        if not changed:
            return gloss_variant
        return _join_comma(gloss_slots)

    def _appended_onomastic_variant(
        self,
        *,
        current_ref: str,
        surface: str,
        analysis_variant: str,
        dulat_variant: str,
        pos_variant: str,
        gloss_variant: str,
        existing_keys: set[tuple[str, str, str]],
        has_other_viable_option: bool,
    ) -> TabletRow | None:
        if self._is_onomastic_pos(pos_variant):
            return None
        if not self._surface_matches_declared_token(surface, dulat_variant):
            return None
        override_entry = self._store.get_entry(dulat_variant)
        if override_entry is None or not override_entry.pos:
            return None

        appended_pos = override_entry.pos.strip()
        appended_gloss = (override_entry.gloss or gloss_variant or "").strip()
        if self._should_prune_pn_append(
            dulat_variant=dulat_variant,
            appended_pos=appended_pos,
            current_ref=current_ref,
            has_other_viable_option=has_other_viable_option,
        ):
            return None
        key = (analysis_variant, dulat_variant, appended_pos)
        if key in existing_keys:
            return None

        return TabletRow(
            line_id="",
            surface="",
            analysis=analysis_variant,
            dulat=dulat_variant,
            pos=appended_pos,
            gloss=appended_gloss,
            comment="",
        )

    def _normalize_onomastic_chars(self, gloss: str) -> str:
        return (gloss or "").translate(_ONOMASTIC_CHAR_MAP)

    def _is_onomastic_pos(self, pos: str) -> bool:
        token = (pos or "").upper()
        return any(tag in token for tag in _ONOMASTIC_POS_TAGS)

    def _has_non_onomastic_viable_option(self, pos_variants: list[str]) -> bool:
        for pos_variant in pos_variants:
            token = (pos_variant or "").strip()
            if not token or token == "?":
                continue
            if "?" in token:
                continue
            if self._is_onomastic_pos(token):
                continue
            return True
        return False

    def _should_prune_pn_append(
        self,
        *,
        dulat_variant: str,
        appended_pos: str,
        current_ref: str,
        has_other_viable_option: bool,
    ) -> bool:
        if "PN" not in (appended_pos or "").upper():
            return False
        if not current_ref:
            return False
        if not has_other_viable_option:
            return False
        return not self._attestation_index.has_reference_for_variant_token(
            dulat_variant,
            current_ref,
        )

    def _surface_matches_declared_token(self, surface: str, dulat_variant: str) -> bool:
        surface_key = self._store.normalize_key(surface).replace(" ", "")
        dulat_key = self._store.normalize_key(_TRAILING_HOMONYM_RE.sub("", dulat_variant)).replace(
            " ", ""
        )
        return bool(surface_key and dulat_key and surface_key == dulat_key)
